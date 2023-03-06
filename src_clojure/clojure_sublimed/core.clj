(ns clojure-sublimed.core
  (:require
    ; [clojure.spec.alpha :as spec]
    [clojure.string :as str])
  (:import
    [clojure.lang Compiler Compiler$CompilerException ExceptionInfo LispReader$ReaderException]
    [java.io Writer]))

(def ^:dynamic *print-quota*
  1024)

(defn- to-char-array ^chars [x]
  (cond
    (string? x)  (.toCharArray ^String x)
    (integer? x) (char-array [(char x)])
    :else        x))

;; modified from nrepl.middleware.print/with-quota-writer
(defn bounded-writer
  "java.io.Writer that wraps throws once it has written more than `quota` bytes"
  ^Writer [^Writer writer quota]
  (let [total (volatile! 0)]
    (proxy [Writer] []
      (toString []
        (.toString writer))
      (write
        ([x]
         (let [cbuf (to-char-array x)]
           (.write ^Writer this cbuf (int 0) (count cbuf))))
        ([x off len]
         (locking total
           (let [cbuf (to-char-array x)
                 rem (- quota @total)]
             (vswap! total + len)
             (.write writer cbuf ^int off ^int (min len rem))
             (when (neg? (- rem len))
               (throw (ex-info "Quota exceeded" {})))))))
      (flush []
        (.flush writer))
      (close []
        (.close writer)))))

(defn bounded-pr-str [x]
  (let [writer (bounded-writer (java.io.StringWriter.) *print-quota*)]
    (try
      (binding [*out* writer]
        (pr x))
      (str writer)
      (catch Exception e
        (str writer "...")))))

;; CompilerException has location info, but its cause RuntimeException has the message ¯\_(ツ)_/¯
(defn root-cause [^Throwable t]
  (loop [t t
         data nil]
    (if (and
          (nil? data)
          (or
            (instance? Compiler$CompilerException t)
            (instance? LispReader$ReaderException t))
          (not= [0 0] ((juxt :clojure.error/line :clojure.error/column) (ex-data t))))
      (recur t (ex-data t))
      (if-some [cause (some-> t .getCause)]
        (recur cause data)
        (if data
          (ExceptionInfo. "Wrapper to pass CompilerException ex-data" data t)
          t)))))

(defn duplicate? [^StackTraceElement prev-el ^StackTraceElement el]
  (and
    (= (.getClassName prev-el) (.getClassName el))
    (= (.getFileName prev-el) (.getFileName el))
    (= "invokeStatic" (.getMethodName prev-el))
    (#{"invoke" "doInvoke"} (.getMethodName el))))

(defn clear-duplicates [els]
  (for [[prev-el el] (map vector (cons nil els) els)
        :when (or (nil? prev-el) (not (duplicate? prev-el el)))]
    el))

(defn trace-element [^StackTraceElement el]
  (let [file     (.getFileName el)
        clojure? (or (nil? file)
                   (= file "NO_SOURCE_FILE")
                   (.endsWith file ".clj")
                   (.endsWith file ".cljc"))]
    {:method (if clojure?
               (Compiler/demunge (.getClassName el))
               (str (.getClassName el) "." (.getMethodName el)))
     :file   (.getFileName el)
     :line   (.getLineNumber el)}))

(defn as-table [table]
  (let [[method file] (for [col [:method :file]]
                        (->> table
                          (map #(get % col))
                          (map str)
                          (map count)
                          (reduce max (count "null"))))
        format-str (str "\t%-" method "s\t%-" file "s\t:%d")]
    (->> table
      (map #(format format-str (:method %) (:file %) (:line %)))
      (str/join "\n"))))

(defn trace-str
  ([t]
   (trace-str t nil))
  ([^Throwable t opts]
   (let [{:clojure.error/keys [source line column]} (ex-data t)
         cause (or (.getCause t) t)]
     (str
       (->> (.getStackTrace cause)
         (take-while #(not (#{"clojure.lang.Compiler" "clojure.lang.LispReader"}
                            (.getClassName ^StackTraceElement %))))
         (remove #(#{"clojure.lang.RestFn" "clojure.lang.AFn"} (.getClassName ^StackTraceElement %)))
         (clear-duplicates)
         (map trace-element)
         (reverse)
         (as-table))
       "\n>>> "
       (.getSimpleName (class cause))
       ": "
       (.getMessage cause)
       (when (:location? opts true)
         (when (or source line column)
           (str " (" source ":" line ":" column ")")))
       (when-some [data (ex-data cause)]
         (str " " (bounded-pr-str data)))))))

;; Allow dynamic vars to be set in root thread when changed in spawned threads

(def settable-vars
  [#'*ns*
   #'*warn-on-reflection*
   #'*math-context*
   #'*print-meta*
   #'*print-length*
   #'*print-level*
   #'*print-namespace-maps*
   #'*data-readers*
   #'*default-data-reader-fn*
   #'*compile-path*
   #'*command-line-args*
   #'*unchecked-math*
   #'*assert*
   #'spec/*explain-out*])

(def ^:dynamic *changed-vars)

(defn track-vars* [vars on-change body]
  (let [before (persistent!
                 (reduce #(assoc! %1 %2 @%2)
                   (transient {})
                   vars))]
    (push-thread-bindings before)
    (try
      (body)
      (finally
        (doseq [var vars
                :let [val @var]
                :when (not= val (before var))]
          (on-change var val))
        (pop-thread-bindings)))))

(defmacro track-vars [& body]
  `(track-vars* settable-vars
     (fn [var# val#] (swap! *changed-vars assoc var# val#))
     (fn [] ~@body)))

(defn set-changed-vars! []
  (let [[vars _] (reset-vals! *changed-vars {})]
    (doseq [[var val] vars]
      (.set ^clojure.lang.Var var val))))

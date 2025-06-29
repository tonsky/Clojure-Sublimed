(ns clojure-sublimed.core
  (:require
   [clojure.spec.alpha :as spec]
   [clojure.string :as str])
  (:import
   [clojure.lang Compiler Compiler$CompilerException ExceptionInfo LispReader$ReaderException]
   [java.io BufferedWriter OutputStream OutputStreamWriter PrintWriter StringWriter Writer]))

(def ^:dynamic *print-quota*
  4096)

(def quota-marker
  {})

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
                 rem  (- quota @total)]
             (vswap! total + len)
             (.write writer cbuf ^int off ^int (min len rem))
             (when (neg? (- rem len))
               (throw (ex-info "Quota Exceeded" quota-marker)))))))
      (flush []
        (.flush writer))
      (close []
        (.close writer)))))

(defn bounded-pr-str [x]
  (let [writer (if (> *print-quota* 0)
                 (bounded-writer (StringWriter.) *print-quota*)
                 (StringWriter.))]
    (try
      (binding [*out* writer]
        (pr x))
      (str writer)
      (catch ExceptionInfo e
        (if (identical? quota-marker (ex-data e))
          (str writer "...")
          (throw e))))))

(defn duplicate-writer ^Writer [^Writer writer tag out-fn]
  (let [sb    (StringBuffer.)
        proxy (proxy [Writer] []
                (flush []
                  (.flush writer)
                  (let [len (.length sb)]
                    (when (pos? len)
                      (out-fn {"tag" tag, "val" (str sb)})
                      (.delete sb 0 len))))
                (close []
                  (.close writer))
                (write
                  ([x]
                   (let [cbuf (to-char-array x)]
                     (.write writer cbuf)
                     (.append sb cbuf)))
                  ([x off len]
                   (let [cbuf (to-char-array x)]
                     (.write writer cbuf ^int off ^int len)
                     (.append sb cbuf ^int off ^int len)))))]
    (PrintWriter. proxy true)))

;; errors

(defn- noise? [^StackTraceElement el]
  (let [class (.getClassName el)]
    (#{"clojure.lang.RestFn" "clojure.lang.AFn"} class)))

(defn- duplicate? [^StackTraceElement prev-el ^StackTraceElement el]
  (and
    (= (.getClassName prev-el) (.getClassName el))
    (= (.getFileName prev-el) (.getFileName el))
    (#{"invokeStatic"} (.getMethodName prev-el))
    (#{"invoke" "doInvoke" "invokePrim"} (.getMethodName el))))

(defn- clear-duplicates [els]
  (for [[prev-el el] (map vector (cons nil els) els)
        :when (or (nil? prev-el) (not (duplicate? prev-el el)))]
    el))

(defn- trace-element [^StackTraceElement el]
  (let [file     (.getFileName el)
        line     (.getLineNumber el)
        cls      (.getClassName el)
        method   (.getMethodName el)
        clojure? (if file
                   (or (.endsWith file ".clj") (.endsWith file ".cljc") (= file "NO_SOURCE_FILE"))
                   (#{"invoke" "doInvoke" "invokePrim" "invokeStatic"} method))

        [ns separator method]
        (cond
          (not clojure?)
          [(-> cls (str/split #"\.") last) "." method]

          (#{"invoke" "doInvoke" "invokeStatic"} method)
          (let [[ns method] (str/split (Compiler/demunge cls) #"/" 2)
                method (-> method
                         (str/replace #"eval\d{3,}" "eval")
                         (str/replace #"--\d{3,}" ""))]
            [ns "/" method])

          :else
          [(Compiler/demunge cls) "/" (Compiler/demunge method)])]
    {:element   el
     :file      (if (= "NO_SOURCE_FILE" file) nil file)
     :line      line
     :ns        ns
     :separator separator
     :method    method}))

(defn- get-trace [^Throwable t]
  (->> (.getStackTrace t)
    (take-while
      (fn [^StackTraceElement el]
        (and
          (not= "clojure.lang.Compiler" (.getClassName el))
          (not= "clojure.lang.LispReader" (.getClassName el))
          (not (str/starts-with? (.getClassName el) "clojure_sublimed")))))
    (remove noise?)
    (clear-duplicates)
    (mapv trace-element)))

(defn datafy-throwable [^Throwable t]
  (let [trace  (get-trace t)
        common (when-some [prev-t (.getCause t)]
                 (let [prev-trace (get-trace prev-t)]
                   (loop [m (dec (count trace))
                          n (dec (count prev-trace))]
                     (if (and (>= m 0) (>= n 0) (= (nth trace m) (nth prev-trace n)))
                       (recur (dec m) (dec n))
                       (- (dec (count trace)) m)))))]
    {:message (.getMessage t)
     :class   (class t)
     :data    (ex-data t)
     :trace   trace
     :common  (or common 0)
     :cause   (some-> (.getCause t) datafy-throwable)}))

(defmacro write [w & args]
  (list* 'do
    (for [arg args]
      (if (or (string? arg) (= String (:tag (meta arg))))
        `(Writer/.write ~w ~arg)
        `(Writer/.write ~w (str ~arg))))))

(defn- pad [ch ^long len]
  (when (pos? len)
    (let [sb (StringBuilder. len)]
      (dotimes [_ len]
        (.append sb (char ch)))
      (str sb))))

(defn- split-file [s]
  (if-some [[_ name ext] (re-matches #"(.*)(\.[^.]+)" s)]
    [name ext]
    [s ""]))

(defn- linearize [key xs]
  (->> xs (iterate key) (take-while some?)))

(defn- longest-method [indent ts]
  (reduce max 0
    (for [[t depth] (map vector ts (range))
          el        (:trace t)]
      (+ (* depth indent) (count (:ns el)) (count (:separator el)) (count (:method el))))))

(defn print-humanly [^Writer w ^Throwable t]
  (let [ts      (linearize :cause (datafy-throwable t))
        max-len (longest-method 0 ts)
        indent  "  "]
    (doseq [[idx t] (map vector (range) ts)
            :let [{:keys [class message data trace common]} t]]
      ;; class
      (write w (when (pos? idx) "\nCaused by: ") (.getSimpleName ^Class class))

      ;; message
      (when message
        (write w ": ")
        (print-method message w))

      ;; data
      (when data
        (write w " ")
        (print-method data w))

      ;; trace
      (doseq [el   (drop-last common trace)
              :let [{:keys [ns separator method file line]} el
                    right-pad (pad \space (- max-len (count ns) (count separator) (count method)))]]
        (write w "\n" indent)

        ;; method
        (write w ns separator method)

        ;; locaiton
        (cond
          (= -2 line)
          (write w right-pad "  " "Native Method")

          file
          (write w right-pad "  " file " " line)))

      ;; ... common elements
      (when (pos? common)
        (write w "\n" indent "... " common " common elements")))))

(defn compiler-err-str [^Throwable t]
  (when (and
          (instance? Compiler$CompilerException t)
          (not (= :execution (:clojure.error/phase (ex-data t))))
          (str/starts-with? (.getMessage t) "Syntax error")
          (.getCause t)
          (instance? RuntimeException t))
    (let [cause (.getCause t)
          {:clojure.error/keys [source line column]} (ex-data t)
          source (some-> source (str/split #"/") last)]
      (str (.getMessage cause) " (" source ":" line ":" (some-> column inc) ")"))))

(defn root-cause ^Throwable [^Throwable t]
  (when t
    (if-some [cause (.getCause t)]
      (recur cause)
      t)))

(defn error-str [^Throwable t]
  (or
    (compiler-err-str t)
    (let [cause (root-cause t)
          data  (ex-data cause)
          class (.getSimpleName (class cause))
          msg   (.getMessage cause)]
      (cond-> (str class ": " msg)
        data (str " " (bounded-pr-str data))))))

(defn trace-str [^Throwable t]
  (or
    (compiler-err-str t)
    (let [w (StringWriter.)
          t (if (and
                  (instance? Compiler$CompilerException t)
                  (= :execution (:clojure.error/phase (ex-data t))))
              (.getCause t)
              t)]
      (print-humanly w t)
      (str w))))

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
  `(track-vars*
     settable-vars
     (fn [var# val#]
       (swap! *changed-vars assoc var# val#))
     (fn [] ~@body)))

(defn set-changed-vars! []
  (let [[vars _] (reset-vals! *changed-vars {})]
    (doseq [[var val] vars]
      (.set ^clojure.lang.Var var val))))

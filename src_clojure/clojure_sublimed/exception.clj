(ns clojure-sublimed.exception
  (:require
    [clojure.string :as str])
  (:import
    [clojure.lang Compiler Compiler$CompilerException ExceptionInfo LispReader$ReaderException]))

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

(defn trace-str [^Throwable t]
  (let [{:clojure.error/keys [source line column]} (ex-data t)
        cause (or (.getCause t) t)]
    (str
      "\n"
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
      (when (or source line column)
        (str " (" source ":" line ":" column ")"))
      (when-some [data (ex-data cause)]
        (str " " (pr-str data))))))

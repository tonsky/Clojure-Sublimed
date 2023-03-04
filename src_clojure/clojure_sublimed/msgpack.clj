(ns clojure-sublimed.msgpack
  (:refer-clojure :exclude [read])
  (:import
    [java.lang.reflect Field]
    [java.io BufferedInputStream BufferedOutputStream BufferedReader BufferedWriter DataInputStream DataOutputStream FilterReader InputStream OutputStream Reader Writer]))

(defn field ^Field [^Class cls name]
  (let [f ^Field (some
                   #(when (= name (.getName ^java.lang.reflect.Field %)) %)
                   (.getDeclaredFields cls))]
    (.setAccessible f true)
    #(.get f %)))
        
(def filter-reader-in
  (field FilterReader "in"))

(def buffered-reader-in
  (field BufferedReader "in"))

(def reader-lock
  (field Reader "lock"))

(comment
  (-> *in* filter-reader-in buffered-reader-in reader-lock))

(def buffered-writer-out
  (field BufferedWriter "out"))

(def writer-lock
  (field Writer "lock"))

(comment
  (-> *out* buffered-writer-out writer-lock))

(defn write-impl [obj ^DataOutputStream out]
  (cond
    (nil? obj)
    (.write out 0xC0)

    (false? obj)
    (.write out 0xC2)

    (true? obj)
    (.write out 0xC3)

    (int? obj)
    (do
      (.write out 0xD3)
      (.writeLong out (long obj)))

    (string? obj)
    (let [bytes ^bytes (.getBytes ^String obj "UTF-8")]
      (.write out 0xDB)
      (.writeInt out (count bytes))
      (.write out bytes))

    (sequential? obj)
    (do
      (.write out 0xDD)
      (.writeInt out (count obj))
      (reduce (fn [_ x] (write-impl x out)) nil obj))

    (map? obj)
    (do
      (.write out 0xDF)
      (.writeInt out (count obj))
      (reduce-kv (fn [_ k v] (write-impl k out) (write-impl v out)) nil obj))
    
    :else
    (write-impl (pr-str obj) out)))

(defn write [obj ^OutputStream out]
  (let [out' (DataOutputStream. (BufferedOutputStream. out))]
    (write-impl obj out')
    (.flush out')))

(defn read-impl [^DataInputStream in]
  (let [tag (.read in)]
    (case tag
      0xC0 nil
      0xC2 false
      0xC3 true
      0xD3 (.readLong in)
      0xDB (let [len   (.readInt in)
                 bytes (.readNBytes in len)]
             (String. bytes "UTF-8"))
      0xDD (let [len (.readInt in)]
             (vec (repeatedly len #(read-impl in))))
      0xDF (let [len (.readInt in)]
             (persistent!
               (reduce
                 (fn [m _]
                   (let [k (read-impl in)
                         v (read-impl in)]
                     (assoc! m k v)))
                 (transient {}) (range len)))))))

(defn read [^InputStream in]
  (read-impl (DataInputStream. (BufferedInputStream. in))))

(require '[clojure.test :as test :refer [deftest is are testing]])
(import '[java.io ByteArrayInputStream ByteArrayOutputStream])

(defn roundtrip [x]
  (let [out   (ByteArrayOutputStream.)
        _     (write x out)
        bytes (.toByteArray out)]
    (do
        (pr x)
        (print " => ")
        (doseq [b bytes]
          (print (format "%02X " (-> b (+ 256) (mod 256)))))
        (println))
    (read (ByteArrayInputStream. bytes))))

(deftest test-roundtrip
  (doseq [x [0 1 -1 Integer/MAX_VALUE Integer/MIN_VALUE Long/MAX_VALUE Long/MIN_VALUE
             nil true false [] [1 2 3] {} {1 2, 3 4} "" "abc" "абв" "\n"]]
    (testing x
      (is (= x (roundtrip x)))))
  
  (is (= ":kw" (roundtrip :kw)))
  (is (= ":ns/kw" (roundtrip :ns/kw))))

(comment
  (test/run-tests)
  
  (roundtrip 0)
  (roundtrip 1)
  (roundtrip -1)
  (roundtrip Integer/MAX_VALUE)
  (roundtrip Integer/MIN_VALUE)
  (roundtrip nil)
  (roundtrip true)
  (roundtrip false)
  (roundtrip [])
  (roundtrip [1 2 3])
  (roundtrip {})
  (roundtrip {1 2, 3 4})
  (roundtrip {:a 1})
  (roundtrip "")
  (roundtrip "abc")
  (roundtrip "абв")
  (roundtrip "\n"))

;;; test.clj: a test file to check eval plugin

;; by Nikita Prokopov
;; October 2021

(ns ^{:doc "Hey!
Nice namespace"
:added ['asdas #"regexp"]
:author "Niki Tonsky"}
  sublime-clojure.test
  (:require
   [clojure.string :as str]))

*ns*

(find-ns 'sublime-clojure.test)

(str/join ", " (range 10))

(defn fun []
  *ns*)

(defn f2
  "Test function"
  ([] (f2 1))
  ([a] (f2 1 a))
  ([a & rest] (println a rest)))

(.getRawRoot #'*warn-on-reflection*)

*warn-on-reflection*

(set! *warn-on-reflection* true)

(.getRawRoot #'*print-namespace-maps*)

*print-namespace-maps*

(set! *print-namespace-maps* true)

*print-namespace-maps*

(alter-var-root #'*print-namespace-maps* (constantly true))

*print-namespace-maps*

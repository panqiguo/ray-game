
(define react-once-until
  (lambda (var effect-ir)
    (react
     :when (not var)
     :then (list
            (effect 'set var true)
            effect-ir))))

(define 逻辑 'logic)
(define 感知 'perception)
(define 意志 'willpower)

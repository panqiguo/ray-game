
(define react-once-until
  (lambda (var effect-ir)
    (react
     :when (not var)
     :then (list
            (effect 'set var true)
            effect-ir))))

(define 理性 'reason)
(define 感知 'empathy)
(define 直觉 'instinct)
(define 强硬 'force)

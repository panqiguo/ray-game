
(define react-once-until
  (lambda (var effect-ir)
    (react
     :when (not var)
     :then (list
            (effect 'set var true)
            effect-ir))))

(define 暴力 'force)
(define 魅力 'charm)
(define 知识 'knowledge)
(define 敏锐 'sense)

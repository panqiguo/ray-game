(define clock-empty?
  (lambda (x)
    (= (clock-value x) 0)))

(define clock-filled?
  (lambda (x)
    (= (clock-value x) (clock-full x))))

(define clock-partial?
  (lambda (x)
    (and
      (> (clock-value x) 0)
      (< (clock-value x) (clock-full x)))))

(define clock-at-least-half?
  (lambda (x)
    (>= (clock-value x) (clock-half x))))

(define reset-clock
  (lambda (x)
    (effect 'set x 0)))

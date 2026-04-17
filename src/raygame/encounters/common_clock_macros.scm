(define clock-half
  (lambda (x)
    (/ (+ (clock-max x) 1) 2)))

(define clock-empty?
  (lambda (x)
    (= (clock-value x) 0)))

(define clock-filled?
  (lambda (x)
    (= (clock-value x) (clock-max x))))

(define clock-partial?
  (lambda (x)
    (and
      (> (clock-value x) 0)
      (< (clock-value x) (clock-max x)))))

(define clock-at-least-half?
  (lambda (x)
    (>= (clock-value x) (clock-half x))))

(define effect-reset-clock
  (lambda (x)
    (effect 'clock- x (clock-value x))))

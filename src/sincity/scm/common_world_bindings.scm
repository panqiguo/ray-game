(define use-world-health
  (lambda ()
    (list
      (list 'health (world-attr 'health)))))

(define use-world-energy
  (lambda ()
    (list
      (list 'energy (world-attr 'energy)))))

(define use-world-money
  (lambda ()
    (list
      (list 'money (world-item 'money 0)))))

(define use-world-food
  (lambda ()
    (list
      (list 'food (world-item 'food 0)))))

(define use-world-basics
  (lambda ()
    (append
      (use-world-health)
      (use-world-energy)
      (use-world-money)
      (use-world-food))))

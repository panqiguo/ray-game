(define world-health-vars
  (list (var 'health (world-attr 'health))))

(define world-energy-vars
  (list (var 'energy (world-attr 'energy))))

(define world-money-vars
  (list (var 'money (world-item 'money 0))))

(define world-food-vars
  (list (var 'food (world-item 'food 0))))

(define world-basics-vars
  (append world-health-vars
          world-energy-vars
          world-money-vars
          world-food-vars))

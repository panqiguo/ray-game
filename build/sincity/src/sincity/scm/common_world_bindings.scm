(define world-health-vars
  (list (import-world-attr 'health)))

(define world-energy-vars
  (list (import-world-attr 'energy)))

(define world-money-vars
  (list (import-world-item 'money)))

(define world-food-vars
  (list (import-world-item 'food)))

(define world-liquor-vars
  (list (import-world-item 'liquor)))

(define world-basics-vars
  (append world-health-vars
          world-energy-vars
          world-money-vars
          world-food-vars
          world-liquor-vars))

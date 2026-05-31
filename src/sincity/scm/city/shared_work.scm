;; Shared work helpers used by multiple scenes.
;; This is not a gameplay module; it is a small authoring helper layer.

(define (make-work-action title desc suit risk ok-money partial-money fail-money fail-health)
  (action
    :title title
    :desc desc
    :check (check
      :suits (list suit)
      :risk risk
      :ok (outcome (list (effect 'add money ok-money)))
      :partial (if (= risk 'low)
        (outcome (list (effect 'add money partial-money)))
        (outcome (list (effect 'add money partial-money) (effect 'add pressure 1))))
      :fail (if (= risk 'high)
        (outcome (list (effect 'add money fail-money) (effect 'add pressure 1) (when (> fail-health 0) (effect 'add health (- fail-health)))))
        (if (= risk 'mid)
          (outcome (list (effect 'add money fail-money) (effect 'add pressure 1)))
          (outcome (list (effect 'add money fail-money))))))))

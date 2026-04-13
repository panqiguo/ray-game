# 常用模板

只在需要开写或重构 `.enc` 时再读本文件。

## 1. 最小 Encounter 模板

```lisp
(encounter
  (id example_id)
  (title "标题")
  (desc "一句话说明这个 encounter。")

(store
  (clock progress "进度" 0 3))

  (reacts
    ((>= (clock-value progress) (clock-full progress))
     (finish 'success)))

  (view
    (scene
      (id root)
      (title "当前局面")
      (desc "玩家现在看到的画面。")
      (show-clocks progress)
      (actions)
      (children))))
```

## 2. 标准 Scene 模板

```lisp
(scene
  (id root)
  (title "标题")
  (desc "描述当前画面、目标和阻碍。")
  (show-clocks alert progress)
  (actions
    some_action
    (when cond another_action))
  (children
    (when cond
      (scene
        (id child)
        (title "子地点")
        (desc "子地点描述")
        (show-clocks progress)
        (actions)))))
```

## 3. 标准 Check 模板

```lisp
(check
  (title "动作标题")
  (desc "玩家是怎么出手的。")
  (suits reason instinct)
  (risk mid)
  (before
    (alert +1))
  (ok
    "成功文案。"
    (progress +1))
  (partial
    "代价成功文案。"
    (progress +1)
    (health -1))
  (fail
    "失败文案。"
    (alert +1)))
```

## 4. 多幕模板

```lisp
(view
  (cond
    ((= phase 'intro)
     (scene ...))
    ((= phase 'pressure)
     (scene ...))
    (else
     (scene ...))))
```

## 5. 什么时候用 `when`

优先写：

```lisp
(actions
  base_action
  (when cond extra_action))
```

不要默认写：

```lisp
(actions
  base_action
  (if cond extra_action nil))
```

`when` 适合：

- `children`
- `actions`
- `show-clocks`

## 6. 长 encounter 的推荐顺序

1. 先写 `store`
2. 再写 `reacts`
3. 再写 `view` 的大分支
4. 最后填动作

如果上来就把长文案和复杂 `if/cond` 混在一起，最容易写坏。

# 常用模板

只在需要开写或重构 `.enc` 时再读本文件。

## 1. 最小 Encounter 模板

```lisp
(include "core_symbols.enc")

(encounter
  (id example_id)
  (title "标题")
  (desc "一句话说明这个 encounter。")

  (store
    (progress (clock "进度" 0 3))
    (phase 'intro))

  (reacts
    ((>= (clock-value progress) (clock-full progress))
     (finish success)))

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

## 3. 标准带检定 Action 模板

```lisp
(action
  (title "动作标题")
  (desc "玩家是怎么出手的。")
  (before
    (alert +1))
  (check
    (suits reason instinct)
    (risk mid)
    (ok
      "成功文案。"
      (progress +1))
    (partial
      "代价成功文案。"
      (progress +1)
      (health -1))
    (fail
      "失败文案。"
      (alert +1))))
```

如果这个行动还需要资源 / 物品 / 手牌，把它们也写进 `action`：

```lisp
(action
  (title "拿钥匙开门")
  (desc "你拿出钥匙，试着直接把门打开。")
  (inputs
    (item car_key 1 "车钥匙" false))
  (before
    (progress +1)))
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

如果 encounter 很长，可以先把公共动作、某一幕的 scene 定义拆到子文件，再在主文件顶部：

```lisp
(include "core_symbols.enc")
(include "black_night/yard.enc")
(include "black_night/entry.enc")
```

## 7. 休息 / 调整 / 重抽类动作模板

很多关键 scene 都值得先检查：是否需要一个“喘口气、换手、重新组织节奏”的动作。

推荐模板：

```lisp
(def breathe
  (action
    (title "休息一下")
    (desc "休息一下。")
    (before
      (reset-hand))))
```

如果不是打斗，也可以把代价改成更贴题的东西，例如：

- `(alert +1)`
- `(tension +1)`
- `(rapport -1)`

默认检查：

1. 这个 scene 是否只有“推进型”动作，没有一个能主动换节奏的动作？
2. 玩家是否需要一个机会来重抽/重整，而不是只能硬着头皮继续推？
3. 如果要给这个动作，代价应该最贴近当前 encounter 的主题。

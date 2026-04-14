# 示例与错误对照

只在需要复杂样例或排错时再读本文件。

## 推荐样例

- 简单两幕：参考 `/Users/usr/Documents/python/ray-game/src/raygame/encounters/teach_thug.enc`
- 树状多地点：参考 `/Users/usr/Documents/python/ray-game/src/raygame/encounters/black_night.enc`

## 可直接复用的小模板

### 1. 最小 `def + action(check)`

来自 `teach_thug`，适合提取公共动作：

```lisp
(def counter
  (action
    (title "防守反击")
    (desc "你先稳住头脸和脚步，再找机会把他顶开。")
    (check
      (suits reason empathy)
      (risk low)
      (ok
        "你稳稳顶住了节奏。"
        (initiative +1))
      (partial
        "你至少没有继续吃亏。"
        (initiative +1))
      (fail
        "你还是没完全顶住。"
        (health -1)))))
```

### 2. 标准两幕 `cond`

来自 `teach_thug`，适合“先脱困，再终结”这类 encounter：

```lisp
(view
  (cond
    ((< (clock-value initiative) (clock-full initiative))
     (scene ...))
    ((< (clock-value opening) (clock-full opening))
     (scene ...))
    (else
     (scene ...))))
```

### 3. `show-clocks` 里按条件显示时钟

推荐用 `when`，不要默认写 `if ... nil`：

```lisp
(show-clocks
  initiative
  (when (> (clock-value knife) 0) knife))
```

### 4. 根地点只负责挂子地点

来自 `black_night`，这是树状 encounter 最推荐的根节点写法：

```lisp
(scene
  (id yard_root)
  (title "院墙缺口")
  (desc "深夜。你站在宅邸外墙的阴影里。")
  (show-clocks alert)
  (actions)
  (children
    (scene ...)
    (scene ...)))
```

### 5. 子地点里用 `when` 控制行动出现

来自 `black_night` 左侧走廊，适合“同一地点里局面随状态变化”：

```lisp
(actions
  (when (= (clock-value patrol) 0)
    left_start_patrol)
  (when (and (= route 'left)
             (> (clock-value patrol) 0)
             (< (clock-value patrol) (clock-full patrol)))
    left_hold_position)
  (when (and (= route 'left)
             (= (clock-value patrol) (clock-full patrol)))
    left_fight_guard))
```

### 6. 树状第二幕

来自 `black_night`，适合“先选入口，再进入同一房间不同版本”的结构：

```lisp
((= phase entry)
 (scene
   (id entry_outer)
   (title "房屋外墙")
   (desc "正门半掩，二楼窗户也留着一点缝。")
   (show-clocks alert)
   (actions)
   (children
     (scene
       (id front_door)
       (actions front_pick_lock front_wait_gap))
     (scene
       (id upper_window)
       (actions climb_window)))))
```

### 7. 同一幕里根据入口切不同版本 scene

如果只是同一地点的不同表现版本，用 `if` 返回两个 scene：

```lisp
((= phase bedroom)
 (if (= entry_method 'front)
   (scene
     (id bedroom_front)
     (actions
       front_direct_inquiry
       bedroom_circle_probe))
   (scene
     (id bedroom_window)
     (actions
       window_direct_inquiry
       bedroom_circle_probe))))
```

## 普通 LLM 最容易犯的错

### 1. 把地点写成“进入/返回动作”

不推荐：

```lisp
(scene
  (id root)
  (actions
    (action (title "进入左侧走廊") ...)
    (action (title "返回院墙缺口") ...)))
```

推荐：

```lisp
(scene
  (id root)
  (actions)
  (children
    (scene
      (id left_corridor)
      (actions ...))))
```

### 2. 乱用裸 clock symbol

不推荐：

```lisp
(= phase entry)
```

推荐：

```lisp
(= phase 'entry)
```

### 3. 本来只需要条件出现，却写成深层 `if ... nil`

不推荐：

```lisp
(children
  (if cond
    (scene ...)
    nil))
```

推荐：

```lisp
(children
  (when cond
    (scene ...)))
```

### 4. 该复用的长 action 不提到顶层 `def`

不推荐在多个 scene 里重复整段：

```lisp
(actions
  (action ... )
  (action ... )
  (action ... ))
```

推荐先提成：

```lisp
(def front_pick_lock
  (action ...))
```

再在 scene 里引用：

```lisp
(actions
  front_pick_lock
  front_wait_gap)
```

### 5. 先写结果，再倒推状态

容易写出“文案通顺、逻辑漂移”的脚本。  
正确顺序是：

1. 先定义局面事实
2. 再定义这些事实如何投影成树
3. 最后再润色文案

### 6. 一个 scene 里塞太多互斥局面

如果同一地点里已经出现：

- 3 个以上互斥 `if`
- 每个 `if` 又各自挂动作组

优先考虑拆成子地点或拆成上层 `cond` 分支。

# 把悬空群岛改造成主线与挑战支路

任务ID：`platformer-01` · 类型：布局与关卡设计 · 难度：中等

## 用户需求

请基于现有悬空平台关卡重新设计从出生点到旗帜的探索路线。主线依次呈现安全起步、台阶式上升、抵达高处旗帜三个清楚的空间段落；同时保留一条离开主线、经过下坠平台和顶碎砖块、再回到主线的可选挑战支路。用金币分布提示前进方向，保留总共14枚金币，主线与支路都要有奖励。沿用原角色、草地平台、下坠平台、砖块与旗帜素材，可以重排或复制平台，但不要只是把整关平移或简单延长一排跳台。

## 初始状态

[
  "原始单关卡直接进入scenes/main.tscn，无标题菜单。",
  "已有14枚金币、3个下坠平台、3个从下方顶碎的砖块。",
  "Player出生点约[0,0.493,0]，旗帜位于[0,3.481,-6]；旗帜只有模型，没有通关逻辑。",
  "平台从出生点延伸到x约-22处；下坠平台分别在[-9,0.419,4]、[-12,-0.315,4]、[-11.753,1.830,-2.306]。"
]

## 可用素材与代码资源

- objects/player.tscn
- objects/platform.tscn
- objects/platform_medium.tscn
- objects/platform_grass_large_round.tscn
- objects/platform_falling.tscn
- objects/coin.tscn
- objects/brick.tscn
- objects/cloud.tscn
- models/flag.glb

## 允许修改范围

- scenes/main.tscn
- objects/platform.tscn
- objects/platform_medium.tscn
- objects/platform_grass_large_round.tscn
- objects/platform_falling.tscn
- objects/coin.tscn
- objects/brick.tscn

## 需要保留

- 保持原角色控制、相机控制、金币收集与二段跳，不提高跳跃高度来掩盖不可达布局。
- 仍从原出生平台出发，保留旗帜作为空间终点，本任务不增加通关系统。
- 保留14枚金币、至少3个下坠平台与3个可顶碎砖块，并保留现有许可证。

## 交付审阅要点（尚未实现自动校验器）

- 人工试玩能从出生点辨认主线方向，用现有二段跳完成三段上升并到达旗帜。
- 挑战支路具有不同风险节奏，绕行有金币奖励且能汇入主线，不是无回路死路。
- 金币在可跳取位置，平台边缘与落点可辨认，主线不要求踩已坠毁平台回头。

## 使用

本任务从共享基础工程 `bases/platformer/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play platformer-01
python3 tools/inputs.py prepare platformer-01 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

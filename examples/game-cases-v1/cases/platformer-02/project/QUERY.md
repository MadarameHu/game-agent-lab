# 给装饰旗帜加入金币门槛与通关流程

任务ID：`platformer-02` · 类型：玩法新增 · 难度：中等偏高

## 用户需求

现在关卡旗帜只是装饰。请新增完整的小关卡目标：收集至少8枚金币后到旗帜处才能通关。金币不足时靠近旗帜应显示还缺几枚，玩家仍能离开继续探索；满足条件时明确提示成功，并显示本次收集数量，提供重新挑战按钮。HUD需要一直显示当前金币和目标数量，让玩家知道为什么在收集。尽量复用现有旗帜、金币UI与音效，不引入新美术包。

## 初始状态

[
  "原关卡有14枚金币，金币脚本避免重复收集，通过Player.coin_collected信号更新HUD。",
  "HUD只有金币图标、乘号和数量；scripts/hud.gd只把收到的数量显示出来。",
  "旗帜直接实例化models/flag.glb，没有Area3D触发器或胜利脚本。",
  "掉到y<-10会重新加载整个场景，同时重置金币、砖块与下坠平台。"
]

## 可用素材与代码资源

- models/flag.glb
- objects/coin.tscn
- objects/player.tscn
- sprites/coin.png
- sounds/coin.ogg
- fonts/lilita_one_regular.ttf

## 允许修改范围

- scenes/main.tscn
- scripts/main.gd
- scripts/hud.gd
- scripts/player.gd
- objects/coin.gd
- scripts/gameplay/ (可新建)
- objects/goal/ (可新建)

## 需要保留

- 保持原平台与14枚金币位置、角色移动和相机手感。
- 金币只能计数一次；保持现有掉落死亡重载行为。
- 保留脚本MIT、素材CC0和字体OFL许可证。

## 交付审阅要点（尚未实现自动校验器）

- 人工分别以少于8枚及至少8枚金币靠近旗帜，能看到缺额提示或通关结果。
- 成功流程不会重复触发，重新挑战恢复金币、角色、砖块和下坠平台。
- 目标进度在游玩时易读，成功后有清楚且可点击的重新挑战入口。

## 使用

本任务从共享基础工程 `bases/platformer/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play platformer-02
python3 tools/inputs.py prepare platformer-02 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

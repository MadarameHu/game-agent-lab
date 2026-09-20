# 改善平台边缘起跳与落地连跳手感

任务ID：`platformer-03` · 类型：操作体验与可用性 · 难度：中等偏高

## 用户需求

请让这个二段跳平台游戏对短促输入更宽容：离开平台边缘后约0.12秒内仍允许一次地面起跳；落地前约0.15秒内按下跳跃，落地时应执行该次起跳。必须保留原有二段跳，但不能借两种缓冲获得第三段跳或无限空中跳跃。保持原移动速度和跳跃高度，在HUD边角增加简短操作提示，说明移动、跳跃及相机控制，避免挡住落点。不要改关卡布局，也不要添加自动跳跃。

## 初始状态

[
  "支持WASD相机相对移动、空格二段跳、方向键旋转相机及手柄输入。",
  "scripts/player.gd直接读取Input.is_action_just_pressed并用jump_single/jump_double布尔值控制跳跃，尚无显式离地计时器或落地输入缓冲。",
  "原控制器离地后仍可能保留jump_single；需要明确区分短暂离地宽容与真正空中跳跃，不能仅追加跳跃机会。",
  "原参数movement_speed=250、jump_strength=7，已有跳跃/落地音效和角色拉伸动画。"
]

## 可用素材与代码资源

- objects/player.tscn
- objects/character.tscn
- sounds/jump.ogg
- sounds/land.ogg
- sprites/coin.png
- fonts/lilita_one_regular.ttf

## 允许修改范围

- scripts/player.gd
- scripts/hud.gd
- scenes/main.tscn

## 需要保留

- 不改变关卡物体transform、金币数、下坠平台和砖块机制。
- 保持原movement_speed=250与jump_strength=7，保留跳跃和落地动画音效。
- 相机旋转、缩放和手柄控制仍可用；提示文字与金币HUD不重叠。

## 交付审阅要点（尚未实现自动校验器）

- 人工在平台边缘刚走空后短按空格仍能起跳；超过宽容窗口不会额外获得地面起跳次数。
- 即将落地前按空格能够接上下一跳，单纯长按不会不停自动跳。
- 连续空中输入不会出现第三次起跳；正常地面起跳加一次空中跳仍保持原手感。

## 使用

本任务从共享基础工程 `bases/platformer/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play platformer-03
python3 tools/inputs.py prepare platformer-03 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

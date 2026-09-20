# 把明亮玩具群岛改为清晰可读的黄昏关卡

任务ID：`platformer-04` · 类型：视觉与信息设计 · 难度：中等

## 用户需求

请在不改变关卡玩法和布局的前提下，把明亮天空群岛调整为温暖黄昏风格：天空和远处云朵形成暖橙到淡紫的层次，角色、金币与平台边缘仍容易识别；下坠平台应通过与普通草地不同的颜色或细节传达危险，不能只靠HUD文字说明。同步整理金币HUD的配色、阴影和留白，使它和场景协调。复用已有模型、材质贴图、字体与粒子，避免给全屏套一层同色滤镜。

## 初始状态

[
  "场景使用scenes/main-environment.tres天空、Sun方向光、objects/cloud.tscn漂浮云和共享models/Textures/colormap.png贴图。",
  "主场景已有14枚金币和3个下坠平台，HUD使用Lilita字体。",
  "scripts/main.gd为Compatibility renderer专门降低太阳和背景能量，视觉修改需要考虑这个既有分支。"
]

## 可用素材与代码资源

- objects/cloud.tscn
- objects/platform.tscn
- objects/platform_falling.tscn
- models/colormap.tres
- models/Textures/colormap.png
- sprites/skybox.png
- sprites/particle.png
- sprites/coin.png
- fonts/lilita_one_regular.ttf

## 允许修改范围

- scenes/main-environment.tres
- scenes/main.tscn
- scripts/main.gd
- objects/cloud.tscn
- objects/platform.tscn
- objects/platform_medium.tscn
- objects/platform_grass_large_round.tscn
- objects/platform_falling.tscn
- models/colormap.tres
- models/Textures/colormap.png
- sprites/skybox.png
- materials/ (可新建)

## 需要保留

- 不改玩法脚本、碰撞形状或世界中物体的位置尺寸；金币数和原始路线保持不变。
- 角色、金币与旗帜的识别度不能因调暗而降低，下坠平台保持原机制。
- 保留原模型、字体许可，新增材质只用项目已有资源。

## 交付审阅要点（尚未实现自动校验器）

- 人工从出生点和远端平台观察，能看出黄昏氛围及前中后景层次，金币与下一落点仍清晰。
- 普通平台和下坠平台有稳定可识别的视觉区分，阴影不遮住落点边界。
- 1280×720窗口中金币HUD不贴边、不覆盖主要落点；兼容渲染模式无明显曝光异常。

## 使用

本任务从共享基础工程 `bases/platformer/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play platformer-04
python3 tools/inputs.py prepare platformer-04 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

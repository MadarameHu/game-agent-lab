# 把摩托车接入主场景并支持停车换车

任务ID：`racing-04` · 类型：车辆适配 · 难度：hard

## 用户需求

把随包提供的摩托车正式接入主场景，启动时默认驾驶摩托车；同时保留黄色卡车作为可选车辆。新增Tab停车换车功能：只有车辆接近静止时才允许切换；切换后新车出现在同一位置并保持朝向，旧车不再响应输入或继续作为活动物理车存在，镜头立即绑定新车并平滑跟随。屏幕角落显示当前是摩托车还是卡车；行驶中按Tab应提示先停车，不应直接换车。摩托车要保留专用侧倾、前叉/车轮动画和发动机声音。

## 初始状态

scenes/vehicle-motorcycle.tscn和scripts/vehicle-motorcycle.gd已经存在，摩托车脚本继承Vehicle并覆盖车身和车轮效果。主场景实际只实例化可驾驶的黄色卡车Vehicle，View.target固定指向它；其他绿、紫、红色卡车是模型实例而非可驾驶控制器。没有车型选择HUD或Tab切换输入逻辑。

## 可用素材与代码资源

- scenes/vehicle-motorcycle.tscn
- scenes/vehicle.tscn
- scripts/vehicle-motorcycle.gd
- scripts/vehicle.gd
- scripts/view.gd
- models/vehicle-motorcycle.glb
- models/vehicle-truck-yellow.glb
- audio/engine-motorcycle.ogg
- audio/engine.ogg

## 允许修改范围

- scenes/main.tscn
- scenes/vehicle-motorcycle.tscn
- scenes/vehicle.tscn
- scripts/vehicle.gd
- scripts/vehicle-motorcycle.gd
- scripts/view.gd
- project.godot
- scripts/vehicle_switcher.gd
- scenes/vehicle_hud.tscn
- scripts/vehicle_hud.gd

## 需要保留

- 保留原赛道GridMap和静态场景布景。
- 两种车辆都保留W/S/A/D和现有音效；摩托车不得只用卡车模型缩放冒充。
- 任何时刻只允许一辆车接受玩家输入，View.target始终有效。
- 保留原始资产及许可证。

## 交付审阅要点（尚未实现自动校验器）

- 初始进入场景驾驶的是摩托车，能看到专用倾斜和前叉/车轮表现。
- 停车时可来回切换，位置朝向保持且镜头和HUD跟随正确对象。
- 行驶中换车被拒绝并有提示；多次切换后没有幽灵车、双重输入或空相机目标。

## 使用

本任务从共享基础工程 `bases/racing/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play racing-04
python3 tools/inputs.py prepare racing-04 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

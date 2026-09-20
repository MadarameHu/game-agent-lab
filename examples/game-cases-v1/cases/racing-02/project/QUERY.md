# 新增按顺序过检查点的单圈计时挑战

任务ID：`racing-02` · 类型：机制添加 · 难度：hard

## 用户需求

在现有赛道上新增一个单圈计时挑战。把现有终点外观所在路段设为起终点，在沿赛道不同位置新增三个有清楚编号的检查点。显示3、2、1、GO倒计时，倒计时结束才允许车辆接受驾驶输入并开始计时。玩家必须按1、2、3顺序穿过检查点，再沿正确方向穿过起终点才结束本圈；反向穿过、漏点或在起终点来回倒车不能完成。HUD显示当前用时和下一个检查点，完成后显示最终用时。新增R键重新开始本次挑战，并重置车辆、计时器和检查点状态。

## 初始状态

项目只有vehicle.gd、vehicle-motorcycle.gd、view.gd三个运行脚本；主场景没有HUD、Area3D检查点、计时器或圈数控制器。track-finish.glb及GridMap中的对应砖仅提供终点视觉外观，不是现成比赛触发器。车辆移动的物理载体是Vehicle/Sphere这个RigidBody3D。

## 可用素材与代码资源

- models/track-finish.glb
- models/track-straight.glb
- models/Library/mesh-library.tres
- scenes/main.tscn
- scenes/vehicle.tscn
- scripts/vehicle.gd
- scripts/view.gd

## 允许修改范围

- scenes/main.tscn
- scenes/vehicle.tscn
- scripts/vehicle.gd
- project.godot
- scripts/race_manager.gd
- scenes/checkpoint.tscn
- scripts/checkpoint.gd
- scenes/race_hud.tscn
- scripts/race_hud.gd

## 需要保留

- 保留原赛道布局、已有模型素材和第三人称跟随相机。
- 保留W/S/A/D基本驾驶方式、车辆音效和烟雾。
- 检测真正穿越触发区和方向，不以按键或固定等待代替过点。
- 保留所有许可证；新增UI和触发器可用Godot内置节点制作。

## 交付审阅要点（尚未实现自动校验器）

- 启动查看倒计时、输入锁定、GO后计时和HUD。
- 按顺序正常驾驶能完成；漏过检查点、逆向过线和起终点反复进出不应完成。
- R后位置、物理速度、计时和已通过检查点全部恢复新一局状态。

## 使用

本任务从共享基础工程 `bases/racing/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play racing-02
python3 tools/inputs.py prepare racing-02 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

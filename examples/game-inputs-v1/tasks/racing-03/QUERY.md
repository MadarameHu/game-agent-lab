# 让卡车的高速转向和镜头更易控制

任务ID：`racing-03` · 类型：驾驶体验 · 难度：medium

## 用户需求

调校默认黄色卡车的驾驶手感：低速仍容易转向，高速连续转向时更平稳，不要突然甩头；保留S先制动再倒车的行为，让松开油门后的减速变化自然。把驱动力、低速/高速转向强度和转向响应速度作为清楚命名的Inspector可调参数，并给出适合当前赛道的默认值。调整跟随镜头，使高速时能提前看见前方道路，减速时平滑回到近景，不要出现镜头跳变。不要改赛道、换车或加入自动驾驶。

## 初始状态

vehicle.gd通过RigidBody3D球体驱动车辆外观，转向使用固定系数4和lerp；倒车目标为负向输入的一半。主要驾驶参数没有导出到Inspector。view.gd按linear_speed把相机z从10插值到20，跟随速度也是脚本固定值。项目已经有前轮转向、车身侧倾、烟雾和随速度改变的引擎音效。

## 可用素材与代码资源

- scripts/vehicle.gd
- scripts/view.gd
- scenes/vehicle.tscn
- scenes/main.tscn
- models/vehicle-truck-yellow.glb
- audio/engine.ogg
- audio/skid.ogg
- sprites/smoke.png

## 允许修改范围

- scripts/vehicle.gd
- scripts/view.gd
- scenes/vehicle.tscn
- scenes/main.tscn

## 需要保留

- 保留现有W/S/A/D与手柄输入映射，不新增自动操控。
- 保留车身、车轮、音效、烟雾和地面对齐效果。
- 保留RigidBody3D球体驱动的整体结构与现有赛道。
- 不得靠降低到近乎不能移动的速度达成稳定效果。

## 交付审阅要点（尚未实现自动校验器）

- 人工比较静止起步、低速弯、高速连续左右转和S制动再倒车。
- Inspector中可找到参数，改动参数确实影响驾驶而非仅改变显示。
- 加速减速时镜头平滑、有前方路况视野且仍跟随玩家。

## 使用

本任务从共享基础工程 `bases/racing/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play racing-03
python3 tools/inputs.py prepare racing-03 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

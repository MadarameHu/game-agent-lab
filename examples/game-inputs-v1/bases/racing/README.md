# Racing 基础工程与四个独立任务

这是 Kenney 官方 **Starter Kit Racing** 的固定commit输入快照。`project/`保留可编辑Godot工程；`briefs.json`包含四个待实现需求，**尚未为这些需求修改任何游戏代码或场景**。每个需求从同一原始工程独立开始，不是四步连续任务。

- 仓库：https://github.com/KenneyNL/Starter-Kit-Racing
- Commit：`2f2e5f2646dda89cb21d4e8539bab60c6e955dc8`
- 下载、哈希、版本和许可来源：`source.json`
- 原始文件哈希清单：`validation/source-files.json`
- 代码MIT；模型、2D图片和音效按原始`project/README.md`说明为CC0-1.0。原始`project/LICENSE`和README均保留；README额外署名了skid音效作者Landeplage。

## 启动与实际初始状态

在Godot Project Manager导入`project/project.godot`，运行主场景`res://scenes/main.tscn`。上游声明Godot4.6、Forward Plus、Jolt Physics；本次使用Godot **4.7.2.stable.official.ed1daf0bf** 做headless导入与运行。

默认可驾驶对象是黄色卡车`Vehicle`，位置`(3.5, 0, 5)`；`View.target`指向它。绿、紫、红色卡车仅是主场景中的模型实例，没有各自驾驶控制器。车辆采用RigidBody3D球体驱動、地面RayCast对齐和独立视觉容器，提供车轮动画、车身侧倾、烟雾、引擎/打滑/碰撞声音。

赛道由GridMap和`models/Library/mesh-library.tres`组成；库含直道、弯道、终点外观、坡道及森林/帐篷装饰。GridMap原始cell数据包含一个终点外观项，但项目只有三个运行脚本（vehicle、vehicle-motorcycle、view），**没有检查点、计时、圈数、赛车HUD或比赛完成机制**。不能把终点外观砖当成已实现的比赛触发器。

完整摩托车场景`scenes/vehicle-motorcycle.tscn`已提供，脚本继承Vehicle并覆盖侧倾、前叉和车轮效果；它尚未作为主场景的可驾驶对象接入。

## 控制

| 输入 | 原始功能 |
|---|---|
| W / 上方向键 / 手柄右扳机 | 向前加速 |
| S / 下方向键 / 手柄左扳机 | 制动，再倒车 |
| A、D / 左右方向键 / 手柄左摇杆X轴 | 转向 |

Input Map还定义了空格`bounce`动作，但当前三个脚本没有使用该动作，不能声称已有跳跃功能。原始工程没有R重开、Tab换车或Esc退出等自定义操作；需要关闭窗口结束原始demo。

## 四个任务

| ID | 类型 | 需求 |
|---|---|---|
| racing-01 | 赛道布局 | 用现有GridMap素材改成带直道和连续左右弯的林间环线 |
| racing-02 | 机制添加 | 新增倒计时、三个顺序检查点、方向敏感起终点、单圈计时和R重开 |
| racing-03 | 驾驶体验 | 参数化并调校低/高速转向、松油门减速与跟随镜头 |
| racing-04 | 车辆适配 | 默认摩托车，新增停车Tab切换黄色卡车及对应镜头/HUD绑定 |

所有`available_assets`和`editable_paths`相对`project/`；资产列表已经逐项检查存在。`editable_paths`中的新脚本或UI场景允许在实现任务时创建，输入包中未预建它们。`acceptance_notes`只提供人类审阅要点，既不是运行时奖励，也不是完成结果。

## 验证结果与范围

`validation/results.json`保存每条实际命令、退出码、耗时和日志路径；单次命令timeout为60秒：

```text
Godot --headless --editor --import --path <project>
Godot --headless --path <project> --quit-after 180 --fixed-fps 60
```

导入与180帧运行均退出0、未超时；没有脚本解析错误或运行期脚本错误。但两个日志均有DummyRenderer退出时shader RID泄漏报告，运行日志另有12个ObjectDB实例、6个resource仍占用的退出清理报告。**这不是无警告通过**，报告按原样保留；未修改上游源码去隐藏它们。

此次只做headless检查，没有开原生窗口，没有截图，也没有人工驾驶或音频检查。180帧固定fps运行用于启动/脚本冒烟，不等于完成一圈驾驶或验证每个视觉资源。主任务会统一进行原生窗口审阅。

Godot导入生成了`.godot/`缓存并更新15个模型的`.import`元数据，具体列表在`source.json`。原始游戏脚本、场景、模型和音效未改动。项目主动关闭FBX导入；运行依赖已提供的GLB和MeshLibrary，不需要安装Blender或额外FBX转换工具。原始`project.godot`的Windows录制输出路径仅是上游编辑器设置，本次未启用录制。

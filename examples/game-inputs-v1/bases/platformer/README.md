# Platformer 初始工程与四个需求

这是 Kenney 官方 Starter Kit 3D Platformer 的固定版本快照，用作后续 agent 开发任务的**原始输入**。本包没有提前完成四个需求，也没有增加奖励函数或通关判定。

- 上游：[KenneyNL/Starter-Kit-3D-Platformer](https://github.com/KenneyNL/Starter-Kit-3D-Platformer)
- 固定 commit：`3fa8a04b1c01ab23db43123d4ce814a34c3fc7f0`，提交日期 2026-03-12。
- 原始工程位于 `project/`，没有嵌套 Git 仓库；下载 URL、ZIP SHA-256、版本与许可详见 `source.json`。
- `upstream-files.sha256` 记录所有上游文件的原始哈希。Godot 首次导入自动改写的 `.import` 元数据和一个二进制资源已恢复成上游原字节；`.godot/` 为本机生成缓存。
- `briefs.json` 是四个独立任务对象的数组。`available_assets` 和 `editable_paths` 都相对于 `project/`；带“可新建”标注的路径是允许后续实现新增内容的位置。

## 启动与操作

上游使用 Godot **4.6 / Forward Plus / Jolt Physics**，已在本机 Godot **4.7.2** 完成 headless 导入和 180 个 process frames 启动检查。

主场景是 `res://scenes/main.tscn`。启动后**直接进入关卡，没有菜单**，方便主 agent 截取真实初始画面。

```sh
GODOT --headless --editor --import --path PROJECT --quit
GODOT --path PROJECT
```

需要兼容渲染时可传 `--rendering-method gl_compatibility`；上游 `scripts/main.gd` 已包含此模式的太阳与背景曝光调整，无须改源码。

- WASD：相对相机移动。
- 空格：跳跃，可以二段跳。
- 方向键：旋转相机。
- 数字小键盘 `+` / `-`：缩放相机；这是上游实际键位，普通主键盘加减号未另行绑定。
- 手柄：左摇杆移动，右摇杆旋转视角，扳机缩放，按钮索引 1 跳跃。
- 上游没有暂停菜单或专用 Esc 退出动作；可关闭应用窗口退出。

## 真实初始内容

`scenes/main.tscn` 有角色、相机、普通/中型/圆形草地平台、3 个下坠平台、14 个金币、3 个可顶碎砖块、7 个云对象及一个旗帜模型。角色出生点约为 `[0,0.493,0]`，旗帜约在 `[0,3.481,-6]`；左侧远端平台延伸到 x 约 -22。

金币拾取更新 HUD；平台被踩后下坠并在低于 y=-10 时删除；砖块从下方被角色顶到后碎裂。角色掉到 y<-10 会重载整个关卡。旗帜现在**只是装饰**，没有胜利逻辑，也没有检查点、金币门槛或结算界面。

四个需求分别是路线拓扑设计、金币门槛与通关流程、跳跃输入宽容性、黄昏视觉与信息层次。每个需求都有依据真实源码填写的初始状态、可用资源、修改范围、必须保留的行为和人工验收说明。这些说明是交给开发者的任务要求，不是已经实现的检查器。

## 验证范围与已知提示

完整命令、耗时、退出码和日志见 `validation/results.json`。导入和启动均返回 0，没有发现脚本解析错误或游戏脚本运行异常；退出时存在 headless DummyShader RID、ObjectDB 和资源释放提示，原始日志予以保留，没有隐瞒为“零警告”。这些短程检查不证明关卡可完整通关，也不代替 native 渲染与人工试玩；本 agent 未打开 native 窗口。

## 许可

代码/工程采用 MIT，原始声明完整保留在 `project/LICENSE.md` 与 `project/README.md`；两个原文件版权年份分别为 2023 和 2026，未擅自统一。上游 README 指明 2D sprites、3D models 和音效采用 CC0。Lilita One 字体另按 SIL OFL 1.1 分发，见 `project/fonts/license.txt`。

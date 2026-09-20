# 第一批游戏任务输入：3 个基础工程 × 4 条需求

已准备平台跳跃、城市建造、赛车三个真实 Godot 工程及配套素材，共 12 个独立任务输入包。三个工程均已在本机导入、启动并实际渲染截图。12条需求是本集合根据源代码和场景编写的任务，不是上游自带的数据标注，也尚未执行。

## 浏览与试玩

打开 **http://127.0.0.1:8766/**，查看三个实际初始场景、筛选任务、展开完整需求与素材范围，并点击“打开初始场景”。原仓库demo审阅页仍使用8765端口。

页面不可用时，在本目录运行：

```bash
python3 tools/serve.py --port 8766
```

保持终端运行。也可以双击 `start-catalog.command`。场景在本机Godot窗口中运行，关闭游戏窗口即可退出；不需要DSW、模型服务或API Key。不要同时打开过多游戏窗口。

| 工程 | 已有初始状态 | 常用操作 |
|---|---|---|
| 平台跳跃 | 角色二段跳、14枚金币、3个下坠平台、3个顶碎砖块、装饰旗帜 | WASD/方向键移动、空格跳跃；相机与手柄操作详见工程README |
| 城市建造 | 自动加载官方示例地图：122个已占用格子、15种结构、余额5860 | 左键建造，右键旋转，Q/E切换，Delete拆除，WASD移动相机，中键旋转，滚轮缩放，F1/F2保存读取 |
| 赛车 | 黄色卡车、拼块赛道、森林和帐篷；摩托车作为可用资源但未接入主场景 | W加速，S制动/倒车，A/D转向 |

目录里的三张截图来自本机当前初始场景，不是作者宣传截图。城市上游默认是空地图；本集合启动适配器加载其现成 `sample map/map.res`，使城市任务从有内容的小镇开始。这一步没有扩建地图或实现任何任务。

## 12条任务

同一工程的四个任务都从同一基础状态独立开始，不按先后顺序叠加成果。

| ID | 任务 | 类型 |
|---|---|---|
| platformer-01 | 重排主线路线和可选挑战支路 | 布局与关卡设计 |
| platformer-02 | 收集8枚金币后到旗帜通关，加入提示与重开 | 玩法新增 |
| platformer-03 | 离地宽容与落地跳跃缓冲，保持二段跳约束 | 操作体验 |
| platformer-04 | 黄昏场景、危险平台识别和HUD协调 | 视觉与信息设计 |
| city-01-civic-square | 保留既有街区，在喷泉旁扩建社区广场 | 布局扩建 |
| city-02-road-stroke | 预览、取消、一次提交的道路拖拽铺设 | 编辑工具 |
| city-03-save-safety | 存读档失败保护、状态提示与重新载入提醒 | 可靠性 |
| city-04-build-palette | 15种结构的分类选择面板与价格显示 | 交互界面 |
| racing-01 | 连续左右弯、直道和外侧布景的练习环线 | 赛道布局 |
| racing-02 | 倒计时、顺序检查点、正确方向过线的单圈计时 | 玩法新增 |
| racing-03 | 高低速转向与随速度变化的跟随镜头 | 驾驶体验 |
| racing-04 | 接入已有摩托车并支持停车换车 | 车辆适配 |

完整用户需求在各 `tasks/<id>/QUERY.md`，机器可读输入在 `task.json`。每条包含：query、实际初始状态、可用资源路径、允许修改范围、需要保留的内容、交付审阅要点、难度、来源和截图引用。

这里的 `acceptance_notes` 只是人工编写的任务要求，不是已实现的校验器、奖励函数或标准答案。当前没有跑这12个任务的生成模型，也没有构建奖励设计agent。

## 输入包的组织

```text
bases/
  platformer/       # 固定版本工程、完整素材、许可证、源文件哈希与日志
  city-builder/
  racing/
tasks/
  <12个任务ID>/
    QUERY.md         # 人可读任务说明
    task.json        # 结构化输入与共享工程引用
previews/
  <3个工程>/
    scene.png        # 实际本机截图
    preview.json     # 场景、引擎与节点信息
    native.log       # 真实启动日志
catalog.json         # 统一索引
VERIFICATION.json    # 输入完整性与启动验证范围
```

在库里，四个任务共享同一个基础工程以避免重复素材。每个task.json都明确路径基准：`initial_project`相对于集合根目录，`available_assets`相对于对应工程；有些资源是可复用脚本或场景，不全是美术模型。`editable_paths`内的括注是可新增文件或修改限制。

要交给coding agent执行，先复制成一个独立、自带素材的工程。不要直接在共享 `bases/` 里开发，否则会污染其他任务的初始输入。

```bash
# 列出任务
python3 tools/inputs.py list

# 直接试玩规定的初始状态
python3 tools/inputs.py play platformer-02
python3 tools/inputs.py play city-01-civic-square

# 打开基础工程编辑器（仅查看；开发应先prepare）
python3 tools/inputs.py editor racing-02

# 复制为新的、独立任务工程。目标目录必须尚不存在。
python3 tools/inputs.py prepare platformer-02 --dest /absolute/path/to/new-workspace
```

复制后的目录包含完整工程、素材、`TASK.json`、`QUERY.md`、来源信息和 `START_INPUT.py`。运行：

```bash
python3 /absolute/path/to/new-workspace/START_INPUT.py
```

它首次运行会导入资源，再进入规定的初始状态。城市会自动加载官方示例小镇；其他两个直接进入原关卡。`--check`可无窗口运行180帧做启动检查，不表示完成或验证了需求。用Godot编辑器直接打开城市工程时，运行后按F3得到同样的初始地图。

## 固定来源、素材与修补

| 工程 | 官方仓库 | 固定commit |
|---|---|---|
| 平台跳跃 | https://github.com/KenneyNL/Starter-Kit-3D-Platformer | `3fa8a04b1c01ab23db43123d4ce814a34c3fc7f0` |
| 城市建造 | https://github.com/KenneyNL/Starter-Kit-City-Builder | `4535092b740b378b700efd9df9e27a631815b84a` |
| 赛车 | https://github.com/KenneyNL/Starter-Kit-Racing | `2f2e5f2646dda89cb21d4e8539bab60c6e955dc8` |

每个base的 `source.json` 保存归档URL、SHA256、版本和许可依据。代码MIT，随包模型、精灵、音效CC0；所附字体有单独的SIL OFL许可证，保留原文件。平台跳跃和城市的上游文件清单、赛车的 `validation/source-files.json` 用于核对原始快照；`effective-snapshot.json` 记录当前可运行工程非缓存文件的哈希。

本机原生运行发现城市builder在鼠标射线不与地面相交时读取null位置。已增加一个空值返回检查，保留上游原件、补丁和有效文件哈希，见 `bases/city-builder/patches/`。这是基础输入可运行性修补，不实现四条城市任务。Godot生成的 `.godot/` 是本地缓存；部分 `.import` 元数据由当前引擎重新生成，来源记录与有效快照分别保留。

## 已做验证与限制

- 3个固定版本工程均执行了headless导入和约180帧启动检查。
- 3个工程均在本机Godot原生渲染120帧并保存截图，退出码0。修补后的最终原生日志没有SCRIPT ERROR。
- 城市启动适配器实际加载122格、余额5860，与官方示例资源一致。
- 12个任务的唯一ID、工程引用、来源哈希、需求文件和103处资源引用已检查。
- 独立复制的城市/平台工程做了首次导入与无窗口启动检查；城市复制包恢复了相同初始地图。
- 启动与渲染检查不等于完整游戏通关测试，更不等于12条新任务已经完成。

上游声明Godot4.6，本机使用已有Godot4.7.2和 `gl_compatibility`。兼容渲染不支持部分SSAA/SSIL效果，平台材质会进行BPTC到RGBA8转换；部分headless或退出日志有shader RID、ObjectDB或resource清理提示。这些记录未隐去，详见 `VERIFICATION.json` 和各base日志；当前截图和启动成功不代表跨版本、跨平台完全无问题。

## 换机器与归档

`game-inputs-v1.zip`（位于此目录旁）包含三个工程、12个任务、素材、预览与工具，排除可重建缓存和试玩会话。解压后安装官方Godot4.6或兼容版本，将 `runtime.json` 的 `godot` 改成可执行文件的绝对路径；第一次打开会自动导入。独立复制包也支持通过 `GODOT` 环境变量指定引擎。

本机当前沿用前一个demo已安装的任务内Godot，路径记录在runtime.json；大型引擎二进制不重复包含在此素材集合中。所有素材、工程、需求和截图均已本地保存，新机器不需要访问DSW。

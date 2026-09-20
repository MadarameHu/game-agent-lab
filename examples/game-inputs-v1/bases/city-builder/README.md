# City Builder · 官方工程与四个开发任务

这是 Kenney 官方 **Starter Kit City Builder** 的固定提交快照，以及基于真实场景和源码设计的四个中文需求。这里准备的是任务输入，**没有实现任务答案**，也没有训练模型。

## 打开与准备初始状态

打开 `project/project.godot`，运行主场景 `project/scenes/main.tscn`。上游工程声明 Godot 4.6，本包用 Godot 4.7.2 做过 headless 导入和启动检查。

**默认启动为空地图，余额为 $10000。四个任务统一从按 F3 加载官方示例地图之后开始。** F3 读取 `project/sample map/map.res`；实测加载后为122个已占用格子、余额 $5860、范围 X=-7…9 / Z=-5…7，喷泉位于 (5,0,4)。15种结构全部已注册到 Builder。

若使用外部统一启动适配器，只需加载原主场景并触发已有 `load_resources` 输入，等一帧后释放；它与F3等价，不属于任务实现。主场景根节点是 `Main`，Builder 相对路径为 `Builder`，绝对路径通常为 `/root/Main/Builder`；方法为 `action_load_resources()`，内部仍检查 `Input.is_action_just_pressed("load_resources")`，直接无输入调用不会加载。无需另改资金、网格或结构索引。不要把上游 README 的宣传截图当作本机实际初始状态。

## 基础操作

| 输入 | 行为 |
| --- | --- |
| WASD | 平移相机 |
| F | 相机回中心 |
| 按住鼠标中键移动 | 旋转相机 |
| 滚轮 | 缩放 |
| 鼠标左键 | 放置当前结构 |
| 鼠标右键 | 当前结构旋转90度 |
| Q / E | 轮换结构 |
| Delete | 拆除光标格子 |
| F1 | 保存到 `user://map.res` |
| F2 | 从用户存档读取 |
| F3 | 从随包官方示例地图读取 |

macOS默认用户存档位置为 `~/Library/Application Support/Godot/app_userdata/Starter Kit City Builder/`。输入包不附带用户存档，也未为用户执行保存。

## 四个任务

具体结构化输入在 `briefs.json`。其中 `available_assets` 和 `editable_paths` 相对 `project/`；`initial_state.source_evidence` 相对本目录。

1. **city-01-civic-square**：保留官方城市，扩建现有喷泉旁的社区休闲区。布局/场景任务。
2. **city-02-road-stroke**：加入预览、取消和合理收费的拖拽铺路。编辑功能任务。
3. **city-03-save-safety**：修复读取失败丢城风险和重复存读档一致性，加入反馈。存档行为任务。
4. **city-04-build-palette**：为15种结构加入不穿透点击的分类选择面板。视觉/交互任务。

`acceptance_notes` 是供人类审阅最终功能的任务描述，不是运行奖励、自动评分脚本或预先通过的测试。每个任务应单独复制基础工程开始，避免相互污染。

## 已有能力与缺口

- 上游包含动态 MeshLibrary、15种可放置结构、简单扣款、拆除、相机和基本Resource存读档。
- `builder.gd` 的 `_ready()` 创建空 DataMap，不自动装载示例地图。
- 没有车辆/居民模拟、交通寻路、城市经济或胜负目标；不要把本工程表述成完成的城市模拟游戏。
- F2当前先清空GridMap再尝试读取；这里记录了该现状，未替任务实现修复。
- 放置逻辑没有余额不足阻止、撤销或拖拽交易；建筑选择主要靠Q/E，界面主要显示现金和一张操作说明图。
- F3加载官方示例地图是准备初始输入；四个需求所要求的广场扩建、铺路工具、可靠存档和分类面板均未预做。

## 来源与许可证

固定仓库：<https://github.com/KenneyNL/Starter-Kit-City-Builder>

提交：`4535092b740b378b700efd9df9e27a631815b84a`。

- 工程代码：MIT，保留 `project/LICENSE.md` 和上游 README。
- 官方包中的2D sprites、3D models与sound effects：上游 README 明确声明 CC0 1.0。
- Lilita One字体：SIL OFL 1.1，保留 `project/fonts/license.txt`。不要把字体与MIT或CC0混称。
- 所有上游文件，包括源码、美术源文件、素材、说明和许可证均保留；未嵌套 `.git`。

精确下载地址、归档 SHA-256、版本、许可范围见 `source.json`；110个原始文件的上游参考哈希见 `source-files.sha256`；有效工程哈希见 `effective-files.sha256`（不含 `.godot` 缓存）。最初导入产生的15个 `.glb.import` 文件变化已恢复，统一预览阶段再使用本地导入缓存。

### 输入基线兼容修复

实际原生窗口启动发现：鼠标射线不与建造平面相交时，`plane.intersects_ray()` 返回 `null`，上游 `builder.gd` 随后读取 `.x` 导致每帧错误。本包仅加入空值保护，此帧跳过光标格子更新、放置和拆除；结构切换、旋转与F1/F2/F3检查仍在保护之前执行。

原件保存在 `patches/builder.gd.upstream`，最小差异在 `patches/0001-ignore-nonintersecting-pointer-ray.patch`，`source.json` 记录前后哈希。**这是让输入基础工程可正常启动的兼容修复，不是四个开发任务的答案。** 广场、拖拽道路、可靠存档、分类面板均未实现。

## 实际验证与边界

`validation/results.json` 保存命令、退出码、时间和日志位置：

- headless editor import：退出码0，无 ERROR。
- 原版主场景 headless启动180帧：退出码0；退出时报告4个ObjectDB实例与2个resource未释放。日志原样保留，未将其伪装为完全无警告。
- 独立只读检查脚本实际触发F3，验证0格→122格及余额变化；完整结构catalog和所有格子见 `validation/sample-map-inspection.json`。

这里没有打开原生窗口，没有验证画面质量、全部鼠标操作或四个未实现的需求。强制退出时的资源泄漏提示为上游现状；这些输入任务是否完成，要由后续开发和实际试玩判断。

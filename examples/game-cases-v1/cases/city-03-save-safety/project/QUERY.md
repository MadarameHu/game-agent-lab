# 让存读档能可靠反馈并保护当前城市

任务ID：`city-03-save-safety` · 类型：存档行为与可靠性 · 难度：hard

## 用户需求

基于加载后的示例城市改进F1/F2存读档：存档和读取成功时给出不挡住建造的清晰提示；存档不存在、损坏或读取失败时解释原因，并完整保留当前城市和余额，不能先清空场景再失败。连续保存两次不同修改后，F2必须读取最后一次真实保存的数据，包括结构位置、类型、旋转和资金。保留F3作为重载官方示例城市的独立操作，并在此操作会丢失未保存修改时提醒用户。不要改写随包提供的官方sample map。

## 初始状态

{
  "kind": "official_sample_map",
  "startup": "Use the collection launcher to load the official sample resource automatically; opening upstream project directly requires F3. The adapter populates existing GridMap and cash from that resource without implementing the query.",
  "default_scene_warning": "上游默认启动为空地图，并非已有小镇。F3加载是任务输入准备，不是任务实现。",
  "resource": "sample map/map.res",
  "occupied_cells": 122,
  "cash": 5860,
  "bounds_xz": {
    "x": [
      -7,
      9
    ],
    "z": [
      -5,
      7
    ]
  },
  "fountain_cell": [
    5,
    0,
    4
  ],
  "source_evidence": "validation/sample-map-inspection.json"
}

## 可用素材与代码资源

- sample map/map.res
- sprites/coin.png
- sprites/instructions.png
- fonts/lilita_one_regular.ttf
- sounds/toggle.ogg

## 允许修改范围

- scripts/builder.gd
- scripts/data_map.gd
- scripts/data_structure.gd
- scripts/
- scenes/main.tscn
- project.godot

## 需要保留

- 保留官方素材许可证与字体许可证。
- 保留原有15种结构资源及其索引语义，已有地图仍可加载。
- 除本任务明确要求外，保留建造、拆除、90度旋转、相机移动/旋转/缩放、F1/F2/F3基本能力。
- 任务从加载官方sample map后的城市状态开始，不把空场景或宣传截图当作实际初始地图。
- 仍使用user://下的用户存档；保留官方res://sample map/map.res不被覆盖。
- 不预生成用户存档，不替测试者提前按下保存或确认。

## 交付审阅要点（尚未实现自动校验器）

- 从示例城市作出修改并存档，继续修改再次存档，重载确认恢复第二次状态而非缓存中的第一次。
- 在独立测试副本里模拟缺失/损坏存档，人工确认城市及余额未丢失且错误提示可理解。
- 用F3触发重载流程，确认未保存修改提醒与确认/取消行为均合理。

## 使用

本任务从共享基础工程 `bases/city-builder/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play city-03-save-safety
python3 tools/inputs.py prepare city-03-save-safety --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

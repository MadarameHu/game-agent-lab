# 把喷泉旁扩成可辨认的社区广场

任务ID：`city-01-civic-square` · 类型：布局与场景扩建 · 难度：medium

## 用户需求

加载官方示例城市后，以现有喷泉广场为中心，在相邻空地扩建一个紧凑的社区休闲区。加入有层次的树木绿地、可辨认的人行铺装，以及至少两种现有住宅模型，让新增建筑的朝向与道路关系合理。保留原有喷泉、所有既有建筑和道路；新区域应有清晰入口接到原有道路，不能靠覆盖现有街区腾地。玩家进入任务版本时能直接看到扩建后的城市，并仍然可以继续正常建造。只使用随工程提供的素材。

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
- models/pavement-fountain.glb
- models/pavement.glb
- models/grass.glb
- models/grass-trees.glb
- models/grass-trees-tall.glb
- models/building-small-a.glb
- models/building-small-b.glb
- models/building-small-c.glb
- models/building-small-d.glb
- models/road-straight.glb
- models/road-corner.glb

## 允许修改范围

- scenes/
- scripts/
- structures/
- sample map/

## 需要保留

- 保留官方素材许可证与字体许可证。
- 保留原有15种结构资源及其索引语义，已有地图仍可加载。
- 除本任务明确要求外，保留建造、拆除、90度旋转、相机移动/旋转/缩放、F1/F2/F3基本能力。
- 任务从加载官方sample map后的城市状态开始，不把空场景或宣传截图当作实际初始地图。
- 保留初始122个格子的类型、位置与朝向；新增内容放在未占用格子，不能修改官方sample map原件，扩建版另存新资源。

## 交付审阅要点（尚未实现自动校验器）

- 人工从总体视角确认喷泉与新增区域形成连贯空间，而非散落道具。
- 对照原始示例地图，检查既有城市未被抹掉，新增区域入口与道路关系可理解。
- 打开任务版本确认扩建布局可见，切换结构并试放一次，原建造功能仍可用。
- 这些是交付审阅要求，不是现成引擎奖励或自动评分器。

## 使用

本任务从共享基础工程 `bases/city-builder/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play city-01-civic-square
python3 tools/inputs.py prepare city-01-civic-square --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

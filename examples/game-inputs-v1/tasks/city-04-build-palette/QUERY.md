# 把Q/E轮换变成可读的建筑选择面板

任务ID：`city-04-build-palette` · 类型：视觉与交互 · 难度：medium

## 用户需求

当前示例城市主要靠Q/E轮换结构，玩家很难知道当前要建什么以及价格。加入紧凑的建筑选择面板，将15种现有结构按道路、建筑、地面与景观分组；每个选项有能对应实际模型的名称和价格，当前选择有明显高亮，并显示余额是否足够。鼠标点击面板应只选择项目，不应穿透到地图放置建筑；Q/E与面板选择状态要保持同步。保持城市为视觉主体，不引入外部图片或字体。

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

- sprites/coin.png
- sprites/selector.png
- fonts/lilita_one_regular.ttf
- structures/road-straight.tres
- structures/building-small-a.tres
- structures/building-small-b.tres
- structures/building-small-c.tres
- structures/building-small-d.tres
- structures/building-garage.tres
- structures/pavement.tres
- structures/pavement-fountain.tres
- structures/grass.tres
- structures/grass-trees.tres
- structures/grass-trees-tall.tres

## 允许修改范围

- scenes/
- scripts/
- structures/
- project.godot

## 需要保留

- 保留官方素材许可证与字体许可证。
- 保留原有15种结构资源及其索引语义，已有地图仍可加载。
- 除本任务明确要求外，保留建造、拆除、90度旋转、相机移动/旋转/缩放、F1/F2/F3基本能力。
- 任务从加载官方sample map后的城市状态开始，不把空场景或宣传截图当作实际初始地图。
- 保留全部15种结构可选，不改变现有价格。
- 不得为了展示余额不足而预先耗尽城市资金，初始仍为示例地图的5860。

## 交付审阅要点（尚未实现自动校验器）

- 人工确认15种结构均能找到，名称和价格对应资源，分组与选中态清楚。
- 点击面板多次后检查地图未意外增添格子；通过Q/E切换时高亮与3D预览同步。
- 在常用窗口尺寸下确认面板可读且不遮挡整个城市，已有现金显示与相机操作仍可用。

## 使用

本任务从共享基础工程 `bases/city-builder/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play city-04-build-palette
python3 tools/inputs.py prepare city-04-build-palette --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

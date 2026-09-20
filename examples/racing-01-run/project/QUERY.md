# 改成带连续左右弯的林间练习环线

任务ID：`racing-01` · 类型：赛道布局 · 难度：medium

## 用户需求

把当前赛道改成一条能从黄色卡车出生点连续开完一圈的林间练习环线。保留GridMap拼装方式，使用现有直道、弯道和终点外观砖；在环线中安排一段至少连续三块直道，以及一组先左后右的连续弯道。把帐篷区安排在赛道外侧，森林不要盖住路面或完全遮挡驾驶视角。赛道不应有断口、重叠接缝或需要倒车才能通过的死路。此次只改路线和布景，不添加圈数、计时或检查点玩法。

## 初始状态

scenes/main.tscn使用一个GridMap和已有MeshLibrary铺设场景，默认Vehicle是出生于(3.5,0,5)的黄色卡车，View跟随Vehicle。当前GridMap内有终点外观砖，但没有判圈或计时脚本。现有赛道碰撞保存在MeshLibrary中；装饰项本身没有碰撞形状。

## 可用素材与代码资源

- models/Library/mesh-library.tres
- models/Library/mesh-library.tscn
- models/track-straight.glb
- models/track-corner.glb
- models/track-finish.glb
- models/decoration-forest.glb
- models/decoration-tents.glb
- models/decoration-empty.glb
- scenes/vehicle.tscn

## 允许修改范围

- scenes/main.tscn
- models/Library/mesh-library.tscn
- models/Library/mesh-library.tres

## 需要保留

- 保留黄色卡车及现有W/S/A/D输入、音效和粒子效果。
- 保留View对Vehicle的有效目标引用；不要替换驾驶控制器。
- 保留所有上游模型、声音文件及许可证。
- 不得以自动驾驶或传送代替可实际驾驶的路线。

## 交付审阅要点（尚未实现自动校验器）

- 编辑器中检查路线确为闭合环线，并能辨认三块连续直道及左右连续弯。
- 人工驾驶一圈，留意接缝碰撞、窄弯卡车通行和树木遮挡。
- 确认帐篷在路线外侧且没有新增比赛计时机制。

## 使用

本任务从共享基础工程 `bases/racing/project` 开始，资源路径均相对于该工程。

在集合根目录运行：

```bash
python3 tools/inputs.py play racing-01
python3 tools/inputs.py prepare racing-01 --dest /absolute/path/to/new-workspace
```

这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。

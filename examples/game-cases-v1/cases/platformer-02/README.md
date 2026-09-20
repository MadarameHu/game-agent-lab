# 金币目标与通关流程

原装饰旗帜现在带真实 `Area3D` 触发区：不足8枚金币时显示缺额并允许离开继续探索；达到8枚后再次走到旗帜完成关卡，停止角色运动，显示实际收集数量及“PLAY AGAIN”按钮。HUD一直显示当前数量 `/ 8` 和目标提示。重开调用正式场景重载，恢复所有金币、砖块、下坠平台和角色。

仅修改 `scripts/main.gd` 与 `scripts/hud.gd`。原世界布局、14个金币位置、玩家控制器、相机、声音、模型和许可证均保持原样。运行：

```sh
GODOT --rendering-method gl_compatibility --path PROJECT
```

`PROJECT` 为本目录 `project/`，Godot路径见集合根目录 `runtime.json`。WASD移动、空格二段跳、方向键旋转相机，小键盘加减缩放。

`verification/behavior.gd` 用测试fixture把角色放入真实金币/终点碰撞区域，验证0与7枚时拒绝、8枚时完成、重复收集不计数和重复进入不重复完成。重开测试先通过产品函数消耗一个砖块与下坠平台，再触发实际按钮 `pressed` 信号，检查新场景恢复。测试明确不声称从出生点人工游玩收集8枚。

同一行为测试在原生渲染运行后保存 `evidence/final/success.png`，其中角色位置和金币收集是受控测试状态；`scene.png` 是普通新开局画面。结果与源码哈希见 `evidence/final/result.json`。人类目标理解、界面可用性和自由探索仍待审阅，`human_review` 与组合奖励为空。

## 主 agent 交叉审查修正

原成功面板因居中锚点加正偏移而出屏，失败截图在 `evidence/root-ui-failure`。已调整为居中锚点加半宽/半高负偏移；新增视口包容检查及真实鼠标点击重开，全部通过。最终预览展示实际成功状态，初始画面保留为 `scene-default.png`。

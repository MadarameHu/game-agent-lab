# platformer-03 — 改善平台边缘起跳与落地连跳手感

增加0.12秒离地宽容和0.15秒落地预输入，保持二段跳与原关卡，并加入边角操作提示。

验收覆盖真实走出测试平台后0.083/0.117秒输入保留空中跳，0.133/0.167秒输入仅允许一次空中跳；耗尽两跳后落地前0.067/0.117秒输入触发落地跳，0.183/0.200秒输入过期。长按1.67秒不自动连跳，第三次空中输入不能重置上升速度。测试专用平面和出生点为明确注入，玩家控制器、角色碰撞体、Input事件与物理过程使用产品代码。native脚本还测试相机旋转/缩放与提示和金币HUD不重叠。

行为证据：`evidence/behavior-final2/behavior.json`。一次近边界检查因计时重复计入输入处理帧而失败；原始失败证据保留在 `evidence/behavior-final`，修正的是测试计时与窗口外样本，未为通过测试改变产品计时窗口。

操作：WASD/左摇杆移动，空格/A键二段跳，方向键/右摇杆旋转相机，+/- 或扳机缩放。跳跃和落地音效、拉伸动画、移动250和跳跃7参数保留。

## 启动

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/project" --rendering-method gl_compatibility
```

直接启动该项目即可游玩。Godot 4.7.2，1280×720，Compatibility renderer。原MIT/CC0/OFL许可文件保留。

## 已执行验证与复查

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --headless --editor --import --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/project" --quit
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/project" --rendering-method gl_compatibility --resolution 1280x720 --script "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/verification/render.gd" -- "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/evidence/final"
python3 "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/verification/preservation.py"
python3 "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/verification/check_result.py"
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --headless --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/project" --rendering-method gl_compatibility --script "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/verification/behavior.gd" -- "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/evidence/behavior-final2/behavior.json"
python3 "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-03/verification/check_result.py"
```

最终结果为 `evidence/final/result.json`，候选与验证器哈希已冻结；`check_result.py`会因文件变化或检查失败而失败。导入后的原始资源重写由执行脚本恢复，详见 `evidence/import/restored-import-rewrites.json`；直接重跑导入可能产生Godot资源格式重写，此时哈希检查会正确报告变化。native渲染批量运行必须先取得 `work/game-batch-11/native-render.lock` 独占锁（本次已取得）。

## 验收边界

- 人工操作手感与实体手柄体验待验收；自动测试用Input action事件驱动物理，并非人类通关。
- 物理测试使用原角色/碰撞体配合测试专用平面与出生点；native截图来自未修改的原关卡。
- 60Hz下计时以1/60秒离散；保留behavior-final失败证据：测试先前重复计入按键处理帧，修正计时后的边界验证见behavior-final2。
- 平台项目没有用户存档读写；测试未生成或修改user://持久存档。
- Godot退出时出现已知资源清理告警，无运行SCRIPT ERROR。

状态：`awaiting_human`；`engine_reward=1`，`human_review=null`，`combined_reward=null`。未把实现者视觉观察计为人工通过。

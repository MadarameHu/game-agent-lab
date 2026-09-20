# racing-04 默认摩托车，Tab停车切换黄色卡车，镜头/HUD绑定及行驶拒绝提示。

启动：`"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/racing-04/project"`

操作：W/S/A/D驾驶，支持原有手柄映射。

Tab停车换车；物理速度小于0.5m/s且驱动状态低于0.08时允许。默认摩托车，切换到黄色卡车，再按Tab切回。行驶中按Tab显示Stop first。原摩托车专用侧倾、前叉、车轮和发动机声音保留。旧车立即从场景移除，新车保持物理位置和模型朝向，镜头目标当帧重绑，角落HUD更新车型。

验证包含两车实际Input驾驶、行驶Tab拒绝、摩托车专用动画、停车换车保持位置朝向和镜头/HUD，以及连续10次真实Tab切换无双车或空目标。

复验命令完整记录于 `evidence/final/result.json` commands。核心脚本为 `verification/behavior.gd`；`verification/preservation.py`核对72个基线文件非editable内容及GridMap一致性。原生截图为 `evidence/final/scene.png`，渲染记录为render.json。

自动硬检查通过，human_review与combined_reward均为null，状态awaiting_human。

- 人工摩托车手感与换车镜头视觉连续性待验收。
- 反复换车测试注入停车状态；两种车实际驾驶及Tab事件均经过运行时输入。

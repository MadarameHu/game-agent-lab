# racing-03 黄色卡车新增速度相关转向、平滑响应及前瞻镜头；驾驶参数Inspector可调。

启动：`"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/racing-03/project"`

操作：W/S/A/D驾驶，支持原有手柄映射。

只修改vehicle.gd与view.gd。Inspector参数 drive_force=100、low_speed_steering=3.4、high_speed_steering=0.95、steering_response=6、coast_response=2；实测水平物理速度2至8m/s连续调整转向。S先制动再倒车；松油门按指数平滑减速。镜头按物理速度平滑从10拉远至19，并沿实际水平行驶方向最多偏移3.5米。

验证包含实际Input起步、S制动倒车、松油门单调减速、高低速转向、连续左右转响应上限、参数实际改变驱动、镜头加减速连续过渡。数值详见behavior.json。

复验命令完整记录于 `evidence/final/result.json` commands。核心脚本为 `verification/behavior.gd`；`verification/preservation.py`核对72个基线文件非editable内容及GridMap一致性。原生截图为 `evidence/final/scene.png`，渲染记录为render.json。

自动硬检查通过，human_review与combined_reward均为null，状态awaiting_human。

- 高/低速手感与前方道路可视性仍待人工验收。
- 高低速转向与镜头阶跃是控制状态的产品函数fixture，实际起步是完整Input+物理。
- 首次导入发现新增函数混用缩进，已修复；保留import.log/behavior-v1.log失败记录。

交叉审查修复：原镜头前瞻误用了负Z朝向，实际Input行驶速度+9.376m/s时，前瞻为-3.116米，点积-29.216。已改为实际水平速度方向，增加真实Input的速度与前瞻点积>1断言，修复后通过。原失败诊断为`behavior-direction-before.json`及同名log，修复前源码另存txt。重新执行完整行为、preservation及原生渲染。`scene-moving.png`展示实际forward输入120物理帧后的镜头；render.json记录当时速度、前瞻和正点积。

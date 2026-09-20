# racing-02 单圈计时挑战

新增3、2、1、GO倒计时，驾驶输入锁定、三个编号检查点、有方向的起终点和计时HUD。W/S/A/D驾驶，R重开。必须依次过1、2、3再正向过终点。

已执行实际输入整圈119.74米，完成用时约55.8模拟秒、最大中心线距离1.90米；实际Area3D穿越fixture覆盖漏点、乱序、逆向、正确过线与R状态复位。测试fixture的初始位置/速度注入与完整Input驾驶分开记录。早期测试失败日志保留，修正等待时序后通过。

启动：`"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/racing-02/project"`

复验命令见 `evidence/final/result.json` 的 commands；实际驾驶脚本 `verification/drive.gd`，触发器测试 `verification/behavior.gd`。原生截图 `evidence/final/scene.png`，渲染信息 `render.json`。

自动检查通过，人工驾驶手感和标记可读性尚待用户验收；human_review及combined_reward保持null。输入资产、许可证与GridMap未修改。

交叉审查修正：起终点标签缩至原1/3并抬高。重新通过import、11项behavior及原生渲染；整圈逻辑未变，保留已完成整圈证据。72个基线文件的非editable部分和GridMap整块逐项核对一致。

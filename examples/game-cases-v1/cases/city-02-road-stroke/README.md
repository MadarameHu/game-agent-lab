# 为道路增加可取消的拖拽连续铺设

道路支持整段拖拽预览、转角衔接、一次提交与Esc取消；重复格去重，遇非道路占用整段拒绝并提示，住宅与绿地保持单格建造。

直接启动：

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/city-02-road-stroke/project" --rendering-method gl_compatibility
```

不要使用 START_INPUT.py，它会覆盖任务启动地图。

验证：verification/test.gd 在独立工程副本、独立 user:// 目录内运行；evidence/final 保存导入日志、真实行为检查、原生截图与完整命令。复跑需先导入隔离副本，再执行 `--headless --script res://.verification/test.gd -- <证据目录>`（复制 verification 为 .verification）。

人工审阅尚未进行，human_review 与 combined_reward 为 null。自动 engine_reward 只表示冻结契约的自动检查是否通过，不代表审美或操作体验评分。

限制：
- 自动转角用于直路与灯柱直路；选择弯道、分叉或十字路时保留手动选型及旋转。
- 快速跨格拖动按X后Z补齐；复杂绕行的操作手感与预览视觉等待人工确认。
- 行为测试使用真实Viewport鼠标事件；为消除headless64x64默认视口和相机插值影响，测试设1280x900视口及已稳定的默认相机。
- Godot退出资源释放警告不属于运行时SCRIPT ERROR。

# 把喷泉旁扩成可辨认的社区广场

在原喷泉南侧新增27格社区庭院：连贯人行铺装、两种住宅、草地与高低树木；直接启动显示149格扩建城市，资金5860。

直接启动：

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/city-01-civic-square/project" --rendering-method gl_compatibility
```

不要使用 START_INPUT.py，它会覆盖任务启动地图。

验证：verification/test.gd 在独立工程副本、独立 user:// 目录内运行；evidence/final 保存导入日志、真实行为检查、原生截图与完整命令。复跑需先导入隔离副本，再执行 `--headless --script res://.verification/test.gd -- <证据目录>`（复制 verification 为 .verification）。

人工审阅尚未进行，human_review 与 combined_reward 为 null。自动 engine_reward 只表示冻结契约的自动检查是否通过，不代表审美或操作体验评分。

限制：
- 美学、住宅朝向与喷泉空间连贯性等待人工确认。
- 自动检查覆盖状态、连通与建造动作；没有模拟长期经营或交通。
- Godot退出时有已知资源释放警告；运行过程中无SCRIPT ERROR。

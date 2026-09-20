# 把Q/E轮换变成可读的建筑选择面板

新增紧凑的三分组15项建筑面板，显示名称/原价、选中高亮与资金状态；鼠标选项不穿透建造，Q/E与面板和3D模型同步。

直接启动：

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/city-04-build-palette/project" --rendering-method gl_compatibility
```

不要使用 START_INPUT.py，它会覆盖任务启动地图。

验证：verification/test.gd 在独立工程副本、独立 user:// 目录内运行；evidence/final 保存导入日志、真实行为检查、原生截图与完整命令。复跑需先导入隔离副本，再执行 `--headless --script res://.verification/test.gd -- <证据目录>`（复制 verification 为 .verification）。

人工审阅尚未进行，human_review 与 combined_reward 为 null。自动 engine_reward 只表示冻结契约的自动检查是否通过，不代表审美或操作体验评分。

限制：
- 名称采用与工程模型对应的英文名称，悬停可见实际模型文件名；未引入外部字体或图片。
- 自动测试使用1280x900和1024x768视口，人工仍需确认常用窗口下城市主体及面板可读性。
- 零余额仅在隔离测试夹具中注入，正式初始余额保持5860；保留原有建造资金规则。
- Godot退出时的资源释放警告未伴随运行时SCRIPT ERROR。

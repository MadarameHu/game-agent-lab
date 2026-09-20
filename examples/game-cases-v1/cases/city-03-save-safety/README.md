# 让存读档能可靠反馈并保护当前城市

F1写完临时档再替换正式档；F2绕过资源缓存并在完整校验后加载，失败保留当前城市与余额；F3对未保存修改提供确认/取消。状态提示不阻挡建造。

直接启动：

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/city-03-save-safety/project" --rendering-method gl_compatibility
```

不要使用 START_INPUT.py，它会覆盖任务启动地图。

验证：verification/test.gd 在独立工程副本、独立 user:// 目录内运行；evidence/final 保存导入日志、真实行为检查、原生截图与完整命令。复跑需先导入隔离副本，再执行 `--headless --script res://.verification/test.gd -- <证据目录>`（复制 verification 为 .verification）。

人工审阅尚未进行，human_review 与 combined_reward 为 null。自动 engine_reward 只表示冻结契约的自动检查是否通过，不代表审美或操作体验评分。

限制：
- 测试通过独立user://目录创建坏档和写入失败夹具，正式工程未生成存档。
- 负例日志含预期的ResourceSaver/Loader文件错误；对应检查验证错误被捕获且城市不变，无SCRIPT ERROR。
- F3自动验证触发真实确认框按钮的pressed信号；键鼠操作体验与提示可读性仍待人工。
- 临时写入及替换降低覆盖失败风险，不声称已验证断电或磁盘硬件故障恢复。

# 场景工坊 · 游戏任务轨迹 Demo

依据 `outputs/game-trajectory-prd/PRD.md` v1.1，实现统一的 12 个任务展示：平台跳跃、城市建造、赛车各 4 个。

启动：

```sh
python3 outputs/game-trajectory-demo/build_data.py
python3 outputs/game-trajectory-demo/server.py --port 8769
```

访问 http://127.0.0.1:8769/ 。工程数据由同级 `game-cases-v1`、`racing-01-run`、`game-inputs-v1` 读取，须保留相对目录布局。

页面包括任务库、中文需求拆分、素材与来源、环境及角色、代码产物差异、标准与检查映射、验证证据抽屉、真实修正记录、实机画面、Godot 试玩和人工审阅。

试玩在 `sessions/` 创建候选运行副本，存档按任务隔离。人工决定只保存到本 Demo 的 `reviews/`，不覆盖原任务历史；真实试玩后再填写。点击「需要修改」仅保存意见，不会自动触发 agent。

模型 ID、原始模型响应与历史完整候选缺失时明确说明；中文过程为依据原始证据整理的展示解读。历史仅提供实际留存文件，旧版本不完整时不能试玩。初始与最终画面可能机位不同，使用并排展示。

这是第一版可交互 Demo：尚未接入模型运行调度、云端串流或完整历史候选恢复。原来的 8767/8768 页面与游戏工程保持原样。

`server.py` 每次操作核验候选、标准、检查器与证据指纹。`racing-01` 只有已保存的局部历史校验，其完整指纹从 Demo 首次启动开始建立；不能反推为过去已有完整审计。

验证：`python3 outputs/game-trajectory-demo/tests_backend.py`。测试使用独立 fixture，不提交真实任务的人审决定。界面与真实数据集成验证结果见后续 `VERIFICATION.json`。

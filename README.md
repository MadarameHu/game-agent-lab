# Game Agent Lab

面向游戏开发 Coding Agent 的可验证任务与实验环境。目标是为 Agentic RL 准备任务、环境、reward 和执行轨迹。

当前提供 **3 个基础游戏工程、12 个任务输入包、12 个已实现案例及历史验证证据**，以及中文轨迹展示界面。包含需求、素材、执行产物、验收条件、检查器、修正记录和效果预览。**尚未实现 RL 训练器；1200 个任务与 200 个 benchmark 是规划，尚未生成。**

## 启动

Python 3.9+，不需要安装 Python 第三方依赖即可浏览。试玩另需 Godot；本机验证版本为 Godot 4.7.2，其他版本未保证兼容。无需模型服务或 GPU 即可查看已有案例。

```bash
python3 scripts/demo.py --port 8769
```

打开 http://127.0.0.1:8769/ 。端口被占用时可换为 `--port 8770`。

试玩按钮会复制案例到独立会话目录，再导入和启动 Godot。配置方法：将 `godot` / `godot4` 加入 PATH，或在启动前设置：

```bash
export GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
python3 scripts/demo.py --port 8770
```

没有 Godot 时仍可查看需求、代码差异、截图和验证证据。人工验收由使用者操作，历史自动检查通过不等于人工验收通过。

## 内容

| 路径 | 内容 |
| --- | --- |
| `examples/game-inputs-v1` | 平台跳跃、城市建造、赛车初始工程及 12 条需求、素材来源 |
| `examples/game-cases-v1` | 后续 11 个实现案例、检查器、失败与成功证据 |
| `examples/racing-01-run` | 首个赛道重排案例及独立验证记录 |
| `examples/game-trajectory-demo` | 统一 12 案例前端、服务与回归测试 |
| `examples/game-world-pipeline` | 较早的仓库场景原型，包含真实 7B 模型调用记录 |
| `examples/task-catalog` | 10 个候选工程、35 个任务方向、扩展与划分规划 |
| `examples/game-trajectory-prd` | 前端 PRD |
| `docs/framework` | 整体架构图和设计说明 |

统一入口为 `scripts/demo.py`。子目录中的早期 README、日志和命令属于历史实验记录；其中的旧 `outputs/` 路径在本仓库对应 `examples/`，旧机器绝对路径不应直接用于新运行。架构图描述目标设计，不代表所有模块已经实现。

## 来源与模型

本项目参考论文 *Agentic Game Development as a Verifiable Trajectory Data Engine for Scaling World Models* 的流程独立搭建，**不是论文代码仓库的 fork，也不是论文模型和指标复现**。论文公开仓库用于研究和核查，没有整体复制到本仓库。

三个游戏基础工程来自 Kenney Starter Kits，案例在这些工程上修改。12 个案例由 Codex coding agents 完成；早期 warehouse 原型才使用 `Qwen2.5-Coder-7B-Instruct`，输出场景操作 JSON。不要把这两组实验混为一谈。检查器和规则目前由开发者 / Codex 编写，并非已训练的 reward model 自动产物。

详见 [来源与许可](docs/PROVENANCE.md)。第三方代码、素材、字体保留原许可；根 LICENSE 仅覆盖本项目新增代码与文档。

## 验证

```bash
python3 examples/game-trajectory-demo/tests_backend.py
python3 scripts/check_bundle.py
node --check examples/game-trajectory-demo/web/app.js
```

后端测试使用人工构造的隔离夹具，不给真实案例写入人工通过。打包检查核对 12 个案例的历史工程、检查器、契约指纹与本地资源链接；它不会重新执行全部游戏行为检查，也不证明检查器覆盖了所有错误。

`racing-01` 的早期记录只有最终场景、受保护资源、检查器和契约的部分历史指纹；完整工程指纹从展示服务首次启动起记录，不能追溯补造。

运行时生成的会话、人工评审、指纹缓存、本机配置均不纳入 Git；模型权重、Godot 安装包、上游论文 checkout 和开发中间目录也不打包。

本次打包验证明细见 [PACKAGING_VERIFICATION.json](docs/PACKAGING_VERIFICATION.json)。赛车样本导入及 180 帧运行退出码为 0，但退出时报告资源未释放；保留原候选工程并记录这一限制。

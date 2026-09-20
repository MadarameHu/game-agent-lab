# 来源与许可

## 项目关系

本项目根据论文 *Agentic Game Development as a Verifiable Trajectory Data Engine for Scaling World Models* 的思路，独立搭建 Godot 替代实验流程。论文： https://arxiv.org/abs/2608.25518 。公开代码： https://github.com/LanceZPF/cardinal-preview ，核查版本 `9536799f0af46bc47b6dfe1bcc38d51b2f35882c`。

论文公开仓库用于阅读与核查，没有整体复制到本项目。当前运行代码未调用其 Unity 生成/训练脚本，不依赖论文权重。本项目不宣称复现论文指标，也不代表论文作者官方实现。

## 打包的第三方工程

| 工程 | 上游仓库 | 固定版本 |
| --- | --- | --- |
| 平台跳跃 | https://github.com/KenneyNL/Starter-Kit-3D-Platformer | `3fa8a04b1c01ab23db43123d4ce814a34c3fc7f0` |
| 城市建造 | https://github.com/KenneyNL/Starter-Kit-City-Builder | `4535092b740b378b700efd9df9e27a631815b84a` |
| 赛车 | https://github.com/KenneyNL/Starter-Kit-Racing | `2f2e5f2646dda89cb21d4e8539bab60c6e955dc8` |

上游脚本为 MIT；其 README 声明随附模型、图像、音效为 CC0。平台跳跃和城市建造的 Lilita 字体另适用 OFL，保留 `fonts/license.txt`。每个基础工程的 `source.json` 记录具体来源和必要的本地适配；任务候选在这些工程之上实现。各工程中的 LICENSE、README 与字体许可按原文保留。

旧 warehouse 示例使用 [Kenney Survival Kit 2.0](https://kenney.nl/assets/survival-kit)，CC0，许可见 `examples/game-world-pipeline/assets/LICENSE-Kenney.txt`。

Godot 为外部运行依赖，未打包可执行文件：https://godotengine.org/license/ 。Qwen 模型权重未打包，模型来源：https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct 。

扩展目录仅记录其他候选来源及许可调查，不等于已经下载、运行或完成这些工程的任务。

## 实验记录的含义

- 12 个游戏开发案例由 Codex coding agents 实现，检查器为人工/agent 编写的程序；没有单独部署训练好的 reward model。
- 早期 warehouse 原型包含 Qwen2.5-Coder-7B-Instruct 的两次真实调用。模型输出场景操作 JSON，与 12 个完整游戏代码案例分开记录。
- 不补造失败尝试、模型身份、人工验收或训练结果。具体轨迹信息以各案例保存的原始记录为准。
- 历史证据包含原机器路径、执行命令和时间戳。它们为实验出处，不是当前安装配置；迁移时保留这些记录及绑定指纹，不篡改为本次运行。
- 本仓库新增文档、入口与展示配置的便携化不改变绑定在历史记录中的候选工程和检查器。

根 MIT LICENSE 仅覆盖本项目新增代码和文档；上游代码、素材和字体保持原有许可。

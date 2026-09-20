# 历史示例：可验证的仓库场景开发流水线

这套项目用公开组件实现了“需求 → LLM 布置场景 → 游戏引擎检查 → 失败反馈 → LLM 修复 → 人类审阅 → 数据导出”。已有两次真实运行、原生 3D 场景和本机试玩。它是按论文思路搭建的最小闭环，不是论文原模型和实验指标的复现。

## 现在就看效果

在这个目录运行 `python3 launch.py review`，再打开 **http://127.0.0.1:8765/**。查看已有记录只需要 Python 3.9+，不需要远端模型或 Godot。原生试玩/重新检查需要自行安装 Godot，见后面的配置步骤。页面可切换：

- **从需求生成**：`warehouse-generate-01`，模型安排六个箱子，首次通过。
- **从失败场景修复**：`warehouse-repair-01`，查看堵路前后、每个检查和真实模型动作。

点 **打开试玩**，会启动本机 Godot 游戏窗口。WASD / 方向键移动，R 回出生点，Esc 退出。先点击游戏画面取得焦点。试玩与历史验证记录分别保存，不覆盖证据。

点 **接受场景** 或 **拒绝** 才记录你的人类决定。当前两条数据都在等你审阅；引擎通过并不等于人类接受。接受后自动写 `review.json`、更新 `manifest.json`、追加 `trajectory.jsonl`，并生成 `sft.jsonl`。

如果网页打不开，在本目录运行 `python3 launch.py review`，或双击 `start-review.command`；保持该终端运行，再打开上面的地址。端口已被占用时，先检查是不是已有审阅服务，不要反复启动。也可以 `python3 launch.py review --port 8766` 使用另一个端口。

## 已经发生的真实结果

| 案例 | 模型调用 | 引擎奖励 | 实际角色移动 | 人类决定 |
|---|---:|---|---|---|
| 从需求布置六个箱子 | 1 | 1.00 | 128 个 60 Hz 物理步后到达出口 | 待审阅 |
| 修复堵路仓库 | 1 | 0.45 → 1.00 | 修复后 176 个 60 Hz 物理步到达出口 | 待审阅 |

两次调用都来自 DSW 上真实的 Qwen2.5-Coder-7B-Instruct 推理。生成使用 755 输入 / 204 输出 tokens，模型推理约 4.35 秒；修复使用 1699 输入 / 62 输出 tokens，推理约 1.30 秒。这里的时间只包含模型推理，不包括引擎验证、SSH或页面操作。

修复案例的初始堵路状态是明确标注的**人工测试输入（fixture）**，不是伪装成模型生成的失败。模型没有删除箱子、缩小箱子或挪动出口，只移动了中间的 `crate_03`：

```json
{
  "moves": [{"id": "crate_03", "position": [2, 0, 0]}],
  "reason": "Moved crate_03 to create a continuous path from player start to goal."
}
```

原位置是 `[0,0,0]`，向东移动 2 米后，墙一样的一排箱子出现缺口。角色穿过缺口，再绕开被挪动的箱子，到达出口。这解释了修复后为什么走了 176 步，而空出直线走廊的生成案例只需 128 步。

## 一条数据具体怎么流动

以 `runs/warehouse-repair-01/` 为例，按下面次序阅读：

1. `manifest.json`：需求、模型来源、运行状态。需求是“布置一个可穿行的仓库，保留六个箱子，从绿色出生点走到金色出口”。
2. `candidates/000-blocked-fixture/scene.json`：初始场景，含房间、出生点、出口、六个箱子的坐标与尺寸。
3. 同目录 `checks.json`：Godot 检查后发现没有可通行路径，奖励 0.45；`scene.png` 是实际渲染。
4. `requests/001-model.json`：完整 LLM 输入。包含固定规则、需求、完整场景和实际失败诊断；它不是只收到一张截图。
5. `responses/001-model.json`：原始模型文本、模型 revision、token 数、耗时。`actions/001-model.json` 是从文本解析的移动动作。
6. `candidates/001-model/scene.json`：程序将动作应用到原场景后的结果。模型只获得移动现有物体的能力，不能修改校验器和目标。
7. 同目录 `checks.json`、`engine.log`、`execution.json`、`scene.png`：第二次独立引擎执行。五个检查通过；176 步到达，最终距目标中心约 0.6357 米。
8. `trajectory.jsonl`：按发生顺序记录请求、响应、场景编辑、引擎验证和等待审阅。真实接受/拒绝发生后会在末尾追加一条事件。
9. `rl_transitions.jsonl`：每个模型候选一条 transition，包含前状态、前检查、模型动作、后状态、后检查、引擎奖励和人类决定。人工 fixture 不冒充模型动作。
10. `sft.jsonl`：只导出通过硬检查且被人类接受的最终模型动作。输入为真实请求 messages，输出为模型 action；最终场景另存 `result_scene`。未接受时文件为空是正常状态。

场景对象的输入输出结构，例如：

```json
{"id":"crate_03","asset":"crate","position":[0,0,0],"size":[1.2,1.2,2],"rotation_y":0}
```

模型动作将 `position` 改为 `[2,0,0]`。单位为米，Y是物体底部高度。房间固定为 12×10×3 米，角色半径 0.30 米，出生点 `[-4,0,0]`，出口 `[4,0,0]`。

这条轨迹是**开发过程的数据**。物理移动的坐标序列在 `checks.json.rollout.path`；此版本保存场景总览截图和采样坐标，没有导出逐帧视频、深度图或像素级动作数据集，也没有训练世界模型。

## 每个 reward 的验证机制

下列权重和阈值是本实现的明确约定，不代表恢复了作者未发布的全部检查器。所有检查都由 Godot/程序执行，LLM不能给自己判通过。

| 检查 | 分值 | 通过标准 |
|---|---:|---|
| scene_load | 0.10 | JSON结构有效、数值有限、至少六个唯一对象、房间/角色/目标符合固定规范；实际加载的 GLB 记录在诊断中 |
| bounds | 0.15 | 每个完整碰撞盒在房间内，边界允许 1 mm 数值容差 |
| no_overlap | 0.20 | Godot `intersect_shape` 查询没有发现物体相交；探测盒总尺寸缩小 4 mm，允许表面贴合 |
| route_exists | 0.25 | 用真实胶囊碰撞查询建立 0.25 m 网格，再用四邻域 BFS 找到路径；胶囊半径 .30 m，额外留 .02 m间隙 |
| rollout_reaches_goal | 0.30 | 真实 `CharacterBody3D.move_and_slide`、重力、60 Hz步进，最多2400步，实际到目标水平距离 ≤ .65 m；连续120步停滞则失败 |

`engine_reward` 是通过项分值之和。初始堵路场景通过前三项，所以是 `.10+.15+.20=.45`；后两项失败，因此整体 `hard_pass=false`。

**全部五项同时通过**才可接受。即使局部得分较高，也不能绕过某个硬检查。

当前导出约定：`combined_reward = hard_pass × (0.65 × human_accept + 0.35 × engine_reward)`。`human_accept` 只有真实用户接受时为1，拒绝为0；尚未审阅时，`human_review`、`combined_reward` 都是 `null`。因此即使引擎通过但用户拒绝，组合值仍为0.35，而SFT不会收录；使用RL导出前应按训练目标明确是否保留这种分值设计。它只是已声明的演示组合规则，没有执行任何梯度更新。

引擎不判断美观、游戏乐趣、真实世界合理性或长期物理稳定性。它仅验证静态、轴对齐箱体场景中的地面通行。有限网格可能漏掉很窄的有效路径；GLB视觉细节的空隙不等于碰撞空隙。

## 用了什么模型、工具、素材

| 部分 | 实际组件 | 职责 |
|---|---|---|
| 场景开发模型 | Qwen/Qwen2.5-Coder-7B-Instruct，Apache-2.0 | 输入文本/JSON，输出物体移动JSON；它是LLM，不是视频世界模型 |
| 历史模型运行 | DSW，A800，Transformers，BF16 | 两次真实推理；新部署须配置自己的 GPU、模型目录和预算 |
| 游戏引擎 | Godot 4.7.2，Mac本机 | 3D渲染、真实碰撞、角色步进和试玩 |
| 资产 | Kenney Survival Kit，CC0 | 箱子等GLB模型和纹理；来源/许可证/哈希在 assets/ |
| 校验器 | `engine/world.gd` | 五个可解释的结构/空间/物理硬检查 |
| 编排器 | Python标准库 `run_pipeline.py` | 调模型、限制动作、调用引擎、保存候选和日志 |
| 审阅/导出 | Python本地服务+HTML/JS | 展示证据、记录用户决定、输出JSONL |

来源：[Qwen模型](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)、[Kenney素材](https://kenney.nl/assets/survival-kit)、[Godot官方发布](https://github.com/godotengine/godot/releases/tag/4.7.2-stable)。

## 重跑

在本目录执行。现有两个运行ID不可覆盖；新运行使用新的ID。新增模型调用前，先按 `deploy/README.md` 部署自己的服务并设置 `GAME_MODEL_SSH_HOST`、`GAME_MODEL_REMOTE_ROOT`。仓库不包含已运行的远端服务或权重。

```bash
# 查看模型服务健康，不消耗推理次数
python3 pipeline/model_client.py --health

# 新生成一个布局，最多尝试2次；受服务剩余预算约束
python3 run_pipeline.py --mode generate --run-id my-generation-01 --max-calls 2

# 修复人工堵路输入，最多尝试2次
python3 run_pipeline.py --mode repair --run-id my-repair-01 --max-calls 2

# 不调用模型，独立重新验证已有最终候选（结果写入rechecks/）
python3 launch.py check --run-id warehouse-repair-01

# 不调用模型，直接打开已有场景试玩
python3 launch.py play --run-id warehouse-repair-01
```

历史服务当时授权5次、使用2次；这些数值是运行证据，不代表新部署的剩余额度。新服务默认最多5次实际推理，失败也计数，计数持久化。模型服务部署、停止、重启见 `deploy/README.md`。查看历史、审阅、引擎检查和试玩均不依赖远端；只有新模型推理需要配置的 SSH 服务连通。

本示例历史验证使用 Godot 4.7.2；仓库不附带引擎二进制。安装 Godot 后，可设置 `GODOT_BIN` 或确保 `godot`/`godot4` 在 PATH，也可用本地配置（`runtime.json` 不提交 Git）：

```bash
python3 launch.py configure --godot /absolute/path/to/Godot
python3 launch.py import
```

Godot 搜索顺序为 `GODOT_BIN`、本地 `runtime.json`、PATH。导入完成后即可独立检查或试玩。`runs/` 中保存的路径、设备与耗时属于原运行记录，不会被当作新机器的配置使用。

仓库整理时仅修改启动/配置适配和说明，历史 `runs/` 与 `engine/` 证据保留原样；旧 `VERIFICATION.json` 描述当时验证，不等于新机器已重新运行。此示例的 LLM 输出是场景移动 JSON；主项目另外12个游戏编码案例的输出与来源见根目录说明。

验证记录见 `VERIFICATION.json`。审阅流程自动测试使用临时测试数据，不会替你接受真实场景。

# racing-01：林间练习环线，一次真实任务执行

自动执行和验证已完成，6/6 项客观检查通过，`engine_reward=1`。最终候选为 `layout-v1`，人工验收待定。打开 http://127.0.0.1:8767/ 查看对比、实际车辆轨迹和试玩入口；W 加速、S 制动/倒车、A/D 转向。

这是一套使用现有开源 Godot 工程与素材实现的替代 pipeline 实例，不是论文原始 Unity 工程或论文模型的复现；本次没有训练模型。

## 这一条数据怎么走完

1. **输入**：`task.json` 保存用户需求、初始状态、素材、允许修改范围及保留项。初始工程来自 `../game-inputs-v1/bases/racing/project`，原始主场景保存在 `evidence/baseline/main.tscn`。
2. **设计验收**：根据需求和原工程写 `contract/acceptance-v1.json`，场景修改前固定。独立审查发现漏查需求中的终点外观，补为 `acceptance.json` v2；保留两个版本及哈希，没有放宽通过标准。
3. **执行**：Coding agent 只修改 `project/scenes/main.tscn` 的 GridMap 数据。排出 18 块道路（11 直道、6 弯道、1 终点外观）、8 组森林和 1 组外侧帐篷。主场景其余内容和 48 个受保护文件保持一致。
4. **验证与诊断**：Python 检查拓扑和文件；Godot 提供真实场景元数据与刚体物理。早期测试驾驶员因路点命中判断有缺陷而停住；修正测试驾驶员后，同一场景通过。开发失败记录和版本保存在 `verification/driver-development`，未把测试工具失败冒充场景修复。
5. **最终验证**：`evidence/final-verification-v2` 保存实际命令、日志、场景、路点、逐物理步 telemetry 和结果。root 另外核验源场景与快照哈希、快照中全部保护文件和 telemetry 连续性。
6. **人工验收**：在本地页面试玩后点击“接受这个结果”或“需要修改”，可填写意见。决定写入 `human-review.json`、manifest 和 trajectory。当前没有替用户提交决定；若提出修改，应根据意见生成下一版候选，再验证。

## 模型、工具与校验器

| 职责 | 本次实际使用 |
|---|---|
| 改场景 | 当前 Codex coding agent，生成布局数据并修改 Godot 文本场景 |
| 设计验收 / 独立审查 | 当前 Codex agents 分角色工作；未调用单独部署的 reward 模型 |
| 最终硬判定 | 可执行 Python / GDScript 检查器，不由 LLM 凭截图打分 |
| 渲染 / 物理 | Godot 4.7.2；原生画面使用 gl_compatibility，物理验收使用 headless |
| 素材 | 输入工程自带 Kenney 道路、森林、帐篷、黄色卡车和声音，保留上游许可证 |
| 自动测试驾驶员 | 外置纯算法跟踪控制器，只注入原 Input actions；没有写车辆位置或速度 |
| 人工 | 驾驶手感、视觉遮挡和设计意图，尚待用户判断 |

没有另行部署开源 LLM、VLM 或 DSW 服务。当前会话底层模型精确名称未被记录，因此不伪填模型名称。这些角色未来可以替换成指定开源模型，但本次证据来自当前 coding agents 与实际引擎运行。

## 每项 reward 的机制与标准

六项分别保留布尔结果；全部为真才得到 `engine_reward=1`。任意一项失败得到 0。`human_review` 和 `combined_reward` 当前为 null，不能理解为已经获得人类认可。

| 检查 | 判定机制 / 标准 | 本次结果 |
|---|---|---|
| project_loads | 新快照导入、实例化主场景，进程正常退出、无超时、无脚本或资源加载错误 | 通过 |
| protected_gameplay | 48 个文件 SHA256 和 GridMap 数据以外的主场景文本一致 | 通过 |
| closed_track | 每块道路端口与相邻砖匹配，全部道路形成单一连通环，无断口/孤岛 | 18 块道路，通过 |
| required_geometry | 至少 3 块连续普通直道；从出生点正向遍历存在相邻先左后右弯；至少 1 块终点外观 | 通过 |
| spawn_and_decor | 出生点在道路上，道路位于原地面内；森林/帐篷存在；变换后的装饰 mesh AABB 不侵入道路带；帐篷在环外 | 通过，视觉仍待人工 |
| physical_lap | 原控制器与刚体，60Hz，最多 18000 步，按序经过整圈路点；局部实际曲线中心线偏差 ≤2.5m，回到物理起点 ≤2m，禁止外部传送/改速度/倒车捷径 | 3519 步，421/421 路点，通过 |

最终跑圈：58.65 秒仿真时间，行驶 134.727m，最大局部偏差 1.993m，返回起点距离 0.355m。仿真可加速运行，这不是墙钟耗时或视频长度。外置测试使用 0.24 的前进输入强度，一次低速跑圈不能证明全速驾驶或所有玩家都能通过。

检查器负例包括：删掉道路砖、移除终点外观、改成没有左右连续弯的合法矩形环线，都在相应门槛失败。拒绝复用非空输出目录，避免读取上次的成功结果。baseline 仅做结构验证，没有执行跑圈；它不满足新任务的几何和布景要求。baseline checker 为 v3，最终 v4 只增加快照来源绑定；对应版本均保留。

装饰没有碰撞形状，因此使用几何包围盒检查道路侵占，不把物理射线当成视觉遮挡证明。两组截图来自真实引擎；俯视相机仅用于取证，产品保持原跟随相机。引擎退出存在已保留的资源/着色器清理警告，不等同于脚本执行失败。

## 输入输出长什么样

输入是 `task.json` + 初始 Godot 工程 + 素材 + 验收规格。执行输出是可运行的 `project/`，同时保存动作依据、候选和哈希。完整任务阶段记录在 `trajectory.jsonl`；逐物理步记录在 `evidence/final-verification-v2/telemetry.jsonl`，包含：

```text
step, position[x,y,z], velocity[x,y,z], heading,
input{forward,back,left,right}, ground,
next_waypoint, local_centerline_distance, traveled
```

输入记录是上一物理 tick 实际施加的 actions，位置是在下一次控制更新前读取。页面使用每 5 步采样的坐标回放，不是游戏录像。原始 JSONL 保序并完整保留。

最终 `result.json` 包含六项 checks、engine_reward、human_review、combined_reward、场景/检查器/driver/contract SHA256 和命令退出状态。该样本当前可标为“自动通过、待人工”，不能标为“最终人类接受”。

## 启动与复验

以下命令在本交付目录 `outputs/racing-01-run` 内执行：

```sh
python3 review/server.py
```

打开 http://127.0.0.1:8767/ 。如果服务已运行，无需重复启动。

`runtime.json` 保存本机 Godot 路径；迁移电脑需修改该路径。可将 `project/project.godot` 导入兼容 Godot 版本启动。保留原输入集合时，完整复验可运行：

```python
import json, subprocess, sys
from pathlib import Path
from datetime import datetime
root = Path.cwd()
godot = json.loads((root / 'runtime.json').read_text())['godot']
out = root / 'evidence' / ('rerun-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
subprocess.run([sys.executable, 'verification/check_racing.py',
    '--project', str(root / 'project'), '--out', str(out),
    '--godot', godot, '--drive'], check=True)
result = json.loads((out / 'result.json').read_text())
assert result['engine_reward'] == 1, result['checks']
```

检查器退出码只表示脚本运行状态，验收请读取 `result.json`。复验默认比较相邻 `game-inputs-v1` 中的初始工程，也可用 `--baseline-project` 指定保存的初始工程目录。复验生成新证据，不会自动覆盖已交付的人审候选。

## 可复用范围

输入、验收规格、候选、日志、失败诊断、独立验证和人工决定这一套格式可以复用到其他任务。平台跳跃需要换成跳跃可达性/碰撞验证，城市建造需要换成地块/道路可达性等检查器；不能直接拿赛道的 reward 当作通用验收。本次还没有实现自动批量调度或训练闭环。

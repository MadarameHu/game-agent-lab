# Racing-01 独立验证器

验证器位于产品工程外部，不向产品加入自动驾驶、检查点或奖励脚本。它读取实际GridMap、原始MeshLibrary和原始车辆，用未改动的Godot物理引擎及控制器完成验证。模型或执行agent的路线计划不作为真值输入。

## 正式证据

- `../evidence/baseline-verification-v2/`：原始布局的结构检查，没有进行原始布局跑圈。
- `../evidence/final-verification-v2/`：冻结候选的结构检查和实际物理跑圈。
- 两次正式结果引用`contract/acceptance.json` v2，SHA256 `75eab0e5fedd27387acd3a3bb166f20eff7bc67cfe7a6a78cb03ea5542711e71`。
- 最终主场景及实际运行快照SHA256均为`c1b7d4c3964d10a88d41536fc1df590be4be6d8173455d06734f58fab69f3ed1`。

最终六个客观检查全部通过。原始车辆在60Hz下运行3519个物理步（包含60步静置），即58.65秒模拟时间；实际行程134.727米，完成421个有序路径点（含起始锚点，依次跨过其余420个门），最大当前局部中心线偏差1.993米，回到物理起点的XZ距离0.355米。整个过程未发出back输入，Sphere最高Y约0.5米。原始RigidBody3D车辆、碰撞、View、控制器保持不变。

基线16块道路已构成闭环，但没有三块连续的纯直道。基线3个帐篷装饰中有1个包络处于环线内部；最终18块道路含所需连续直道与相邻左转、右转，保留1块终点外观、8块森林、1块位于环线外侧的帐篷。原始布局没有执行物理跑圈，因此不能把其`physical_lap=false / not_run`解释为物理不可驾驶。

`result.json`含各检查布尔值、源码/快照/验证器/driver/契约哈希、每个进程完整命令及exit/timeout状态。`topology.json`含道路遍历、转弯符号、装饰包络检查；`route.json`是从现场GridMap独立导出的中心线；`lap.json`是跑圈摘要；`telemetry.jsonl`保留每一个物理步。

最终`engine_reward=1`仅表示固定客观门槛通过。`human_review`和`combined_reward`保持null；驾驶感受、视觉遮挡和林间氛围需要用户审阅，不能由本次自动驾驶通过代替。

## 复跑

从工作区根目录执行，`--out`必须是新目录，不能重用任何非空证据目录：

```bash
python3 outputs/racing-01-run/verification/check_racing.py \
  --project outputs/racing-01-run/project \
  --out outputs/racing-01-run/evidence/a-new-verification-run \
  --godot work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot \
  --drive
```

省略`--drive`只检查结构。验证器复制输入项目到`work/racing-01/validator/cases/`的独立快照，显式`--editor --import --quit`后再加载，不修改传入项目。单条Godot进程timeout为60秒。加载检查必须所有相关进程exit0、未超时，且没有资源/脚本错误。已知引擎退出清理的RID/ObjectDB/resource泄漏报告保留日志，但不归类为运行期资源加载失败。

原始基线由当前已保护文件副本恢复预先保留的`evidence/baseline/main.tscn`构造，详见`baseline-source.json`；没有修改输入库。正式baseline运行使用归档的final-v3 checker；随后final-v4只补充了快照哈希绑定与`source-main.tscn`复制，验收门槛及driver未变。baseline的相同快照哈希有单独`snapshot-integrity.json`补证，原`result.json`未改写。

## 几何语义

已通过Godot加载官方MeshLibrary、读取碰撞顶点确认：

| Tile | 端口 |
|---|---|
| item4终点、item6直道，orientation0/10 | local世界格轴N/S |
| item4/item6，orientation16/22 | E/W |
| item3弯道，orientation0 | W/S |
| item3弯道，orientation10 | E/N |
| item3弯道，orientation16 | E/S |
| item3弯道，orientation22 | W/N |

只接受上述水平四个旋转、Y=0道路格。每个道路端口都必须与邻格反向端口匹配，所有道路组成一个连通环，中心线没有非邻接自交。遍历从原始出生格出发，固定为原车头+Z方向，不为了通过左右弯要求反转路线。左转为正，要求相邻正转和负转；连续直道只计item6，终点不充作纯直道，同时至少保留1个item4终点。

原GridMap缩放0.75、cell_size9.99，世界格距7.4925米。直道中心线沿道路端口，弯道按官方半径5local单位生成四分之一圆弧，世界半径3.75米，每段不超过0.3米。官方砖宽10与格距9.99存在约0.0075米接缝重叠，去重容差0.02米；不把设计接缝误判成断裂。

侧墙内缘约local±4.5，路面半宽约3.375米。森林/帐篷取真实mesh的世界AABB，检查与中心线道路带的距离。AABB包含空角，检查具有保守性；它不等于mesh精确三角形相交。帐篷包络角点须全部在环线中心线多边形外，且包络与道路带不交；至少保留森林和帐篷各一块。森林没有碰撞体，验证器**没有**使用普通Physics ray伪称其不会遮挡镜头。

## 实际驾驶语义

`drive_lap.gd`只调用原来的`Input.action_press/release`，常量forward强度0.24，局部pure pursuit前视1.8米，back始终释放。它不会写Sphere/Container/Vehicle的位置、变换、线速度、角速度、freeze、碰撞或控制器状态，也不手动推进控制器。原始`vehicle.gd`自身写入球体角速度是保留的原有动力学。

物理位置来自`Vehicle/Sphere.global_position`，不能用不随球体移动的Vehicle根节点代替。每步检查当前顺序路径段的XZ误差≤2.5米；只能通过下一个垂直航点门后把索引加一，不在全环寻找最近点，不跨S弯跳段。必须覆盖全部421个路径点（起始锚点加后续420个门）再返回原物理起点XZ半径2米内才完成。达到18000步仍未完成时报告`driver_budget_exhausted`，不会自动诊断人类也无法驾驶。

包含60步静置，之后Sphere Y需位于[-0.25,1.25]米，连续离地不得超过10步，离地时禁止推进航点；单步位移超过1米报告异常。所有观测从真实物理状态读取。日志`input`记录该观测之前一物理步实际施加的Input强度，`input_timing`明确说明时序；接着测试driver才计算下一步输入。

## 工具调试与负例

`driver-development/dev001/`保留首版driver、失败日志及540步轨迹。v1要求靠近每个航点0.85米，即使车辆位于许可路带，也可能因转弯偏移而让航点索引滞后；它在同一候选上失败，**不是执行agent生成的新坏赛道**。

`driver-development/dev002/`保留v2调试结果和源码。v2改为上述顺序垂直航点门；固定2.5米、18000步、2米返回半径和原驾驶参数没有放宽，候选主场景哈希始终相同。最终v3 driver只更正真实Input日志时序和参数说明，没有改变车辆轨迹。正式最终使用v3 driver。

工具审查还补上新鲜输出目录要求、进程exit/timeout检查、60Hz检查、显式导入退出，以及运行快照哈希绑定。这些是验证工具修正，不是赛道修复。

`negative_checks.py`对元数据副本验证三种失败：移除一块路导致断口；把终点换为普通直道，闭环仍在但终点要求失败；构造有终点和足够直道、四个同向弯的矩形环，左右相邻弯要求失败。三项结果见`negative-control-results.json`，使用的元数据另存`negative-fixture-metadata.json`；没有改动产品项目。`versions/`保存正式验证器源码与哈希，供审查追踪。

# racing-01 验证器独立审查

审查对象：`verification/check_racing.py`、`inspect_scene.gd`、`drive_lap.gd`，以及冻结的 `contract/acceptance.json`。这是静态代码审查及两张已生成图片的模型视觉检查，不是用户接受，也不代替实际验证输出。

初次审查代码快照：

| 文件 | SHA-256 |
| --- | --- |
| check_racing.py | db2056780497e5f1991fb4e0efa2e6a3674d7595d76b16dffc6c649327101d6a |
| inspect_scene.gd | b8acc75dba46ef809e46b7eef71eb3ab7f55408756aded623a351481d2459c02 |
| drive_lap.gd | f10cde1068171691ca366efbe75086161f879832b7895af9b5dd3847161ff079 |

## 已确认正确落实的部分

1. **读取真实运行时场景。** inspect脚本加载实际main场景，通过GridMap API读取cell、item、orientation、世界中心和mesh AABB；没有读取布局agent的决策文件。当前固定库的mesh_transform均为identity，代码的AABB转换适用于这份被保护的库。
2. **源文件冻结。** protected-files哈希保护原控制器、车辆、声音、素材和项目配置；main文本只豁免GridMap data，车辆出生、View.target、Camera、地面和其他节点仍被比较。当前主场景非GridMap范围不能加autopilot或lap玩法。外部driver未置于产品工程。
3. **道路拓扑。** 只允许3/4/6作为道路，平面orientation白名单、y=0、双端口匹配、全体道路连通、从出生前向完整遍历一次都实现了。连续三块item6直道与按行驶方向有符号的相邻左-右弯被实际检查。
4. **真实物理而非位置插值。** driver读 `Vehicle/Sphere.global_position` / `linear_velocity`，读Container朝向；对产品的写入仅为Input动作。没有写车辆position/transform/velocity、freeze或controller状态。原脚本给Sphere角速度增量仍正常执行。外部测试模拟驾驶存在，但最终可玩产品没有自动驾驶。
5. **S弯不全局跳段。** `next_index`只按顺序增加1，只有接近下一个waypoint才推进；偏离测量使用当前局部段，不用全环最近点；lookahead也只向前遍历局部有序点列。没有看到把进度直接跳到另一条相邻路段的代码。
6. **掉落与连续性。** driver检查Y范围、最多连续10步不接地、单步XZ位移≤1m；记录每步物理状态。返回起点必须在整条ordered waypoint列表完成后，不会出生即成功。settle60步计入18000步总预算。
7. **装饰不是简单空格检查。** 已按变换后mesh AABB对道路中心线带求距离，至少保留森林、帐篷，并检查帐篷AABB角点在简单环线外。虽然“所有角点在外”单独不足以排除横跨polygon，但与对全部边段的road-band clearance检查联用，可拦截边界穿越或把整条环线包住的大AABB。
8. **人类监督保持缺失。** 输出human_review和combined_reward仍为null，装饰/camera可读性明确保留人工判断；没有MLLM伪装人类奖励。

## 已通知root与验证agent的实质问题

### P1：复用out目录可能读取上次成功工件

初版check_racing.py约141–152行，无条件从 `out/scene_metadata.json`、`out/lap.json` 存在与否读取结果，没有在开始时保证新目录，也没有要求相应command退出0且未超时。`load_good`只看meta存在与日志中没有 `SCRIPT ERROR`，一些普通ERROR/timeout不被拒绝。

后果：若同一个out曾有成功结果，本次inspect或drive失败，旧结果可能被归到当前候选；即使scratch项目独立，也不能阻止out中的旧证据污染。

建议采用**拒绝任何非空输出目录**或每次唯一证据子目录，并同时要求import/inspect成功退出且未超时、drive成功退出且未超时后才接受lap。失败仍保存本次命令日志，不能回落旧文件。

验证agent已回复将按非空out拒绝、command成功状态绑定处理；需要以最终文件和实际新目录运行结果复核，不能仅凭口头修复宣布通过。

### P2：终点外观只统计，没有加入结果门槛

初版geometry报告 `finish_tiles`，但required_geometry只有“三直道＋左-右弯”。因此移除全部finish砖、替换为普通直道仍可能通过全部硬检查。task原文要求使用现有直道、弯道和终点外观砖，不能遗漏。

建议required_geometry增加finish_tiles≥1，明确这是补全原任务要求，不是降低或暗改为通过候选的标准。冻结contract中原本也漏写此项，应保留版本变动说明。现有候选本来有1块finish，不会靠这个修复改善它的结果。

验证agent已回复将纳入并通知root。

### P2：固定60Hz应作为实际结果条件

driver记录 `Engine.physics_ticks_per_second`，但初版main未检查它等于60，simulation_seconds直接按step/60计算。命令 `--fixed-fps 60` 是运行时间设置，不应作为读取实际物理tick的替代证据。固定输入项目目前使用默认60，因此当前预期成立，但验收应明确检查实际记录值。

验证agent已回复将加入60Hz检查。

## 非阻塞边界及建议

- **driver失败分类有保留，但需正确呈现。** 拓扑不成立时不跑driver；跑圈有budget_exhausted、local_centerline_limit_exceeded、vehicle_left_ground_band等status，result还明确写单driver失败不证明人类不能驾驶。这满足基本区分。聚合engine_reward=0只能解释为“当前验证尚未全部通过”，不要把local deviation自动表述为项目故障已证实；也可能是测试driver控制不佳。
- **失败的process与成功的lap绑定。** 新修复应拒绝“lap.passed=true但进程最终报SCRIPT ERROR/timeout”的状态；不能只修文件新鲜度而仍忽略进程执行状态。
- **证据与源码应属于同一快照。** 当前先copytree再从原project计算保护哈希，最后再次从原project计算source_main_sha256。如果有人并发编辑project，可能出现“测的是旧snapshot，报告绑定的是新source”。本轮root可通过不并发改候选规避；通用化时应从snapshot计算所有验收哈希，或检查开始/结束source哈希一致再签出结果。
- **装饰近似是保守几何筛查，不是视觉遮挡。** road_band_half_width=3.375、corner_radius=3.75为固定库几何常数；库被冻结时适用。AABB包含空地和树冠间隙，会误拒一些视觉上可用的摆放，不能把它称为精确mesh交叠。原Physics ray仍看不见无collider装饰，当前代码没有冒用它证明camera无遮挡。
- **中心线采样与车身。** 20段四分之一圆与0.3m直线间隔是有限采样；2.5m是球体中心相对该曲线的容差。它证明库存球体驱动车辆可完成，而非精确车壳几何绝不压线。原任务没有要求更复杂车辆碰撞重建，保留说明即可。
- **移动车辆记录。** driver写入telemetry在发出本步新steer之前，steer字段基本对应上一控制值；第一settle后帧forward字段已经显示throttle但实际press发生在稍后。它不构成运动造假，但消费输入与下一步命令最好分字段，避免逐帧因果分析错一帧。
- **不可见新增文件。** protected-files目前检查已有文件是否更改，不拒绝额外文件。由于main、project.godot、脚本都被冻结，新增未引用文件目前不能自动获得控制权，但交付清单最好把新文件也披露，避免“完全只改GridMap”的叙述超过检查范围。

## 两张native图片的观察（非人类验收）

已查看 `evidence/layout-v1/overview.png` 与 `driver-view.png`：总览中可辨认单条环线、连续弯、终点门、森林和外侧帐篷区；没有从这张总览看见明显道路断口。出生视角中黄色卡车和附近路面可见，终点门及右侧树木占据部分画面，但未完全遮住该时点车辆。

这些仅是两张静态画面的模型观察，**不能证明全圈每个驾驶时点都无遮挡，也不代表人工已经驾驶或接受**。人工审阅仍应保持pending；最好补充真实跑圈不同位置的原跟随相机采样，而不是只保留起点。

## 最终交付前建议

修复上述三项后，使用全新证据目录重新运行，保存checker/driver/contract以及候选snapshot哈希。报告可以说明“自动几何与一次输入驱动真实物理圈通过”，但视觉、手动驾驶与最终human_accept必须继续分离。

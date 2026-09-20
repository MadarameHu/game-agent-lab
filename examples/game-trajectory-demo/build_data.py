#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only source adapter. Chinese text is a 2026-09-20 display explanation.
No model invocation or historical candidate/review is synthesized.
"""
import hashlib,json,pathlib,re,shlex
from urllib.parse import quote,unquote
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE.parent
BATCH=OUT/'game-cases-v1'; INPUTS=OUT/'game-inputs-v1'; RACE=OUT/'racing-01-run'
def read(p,default=None):
 return json.loads(p.read_text()) if p.exists() else default

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def url(p):
 for key,base in [('batch',BATCH),('racing01',RACE),('inputs',INPUTS)]:
  try:return '/files/'+key+'/'+quote(str(p.relative_to(base)),safe='/')
  except ValueError:pass
 raise ValueError(p)
def ev(p,label=None):return {'label':label or p.name,'url':url(p)}
# title, standard, actual method, observed result, optional disclosed fixture.
COMMON={
 'preservation':('原有玩法与素材保留','允许修改范围以外的文件、原场景边界与资源应保持原样。','对照冻结基线哈希，并检查场景中的受保护节点或布局。','保留性检查通过；逐项文件差异见原始证据。'),
 'source_preserved':('控制器和资源保持原版','仅允许调整本任务声明的关卡布局。','比较原始基线与当前工程的文件哈希。','除了允许的主场景，其余基线文件一致。'),
 'preservation-files':('示例地图与资源保留','官方地图、15种结构索引、价格与许可证不得改变。','逐文件对照冻结基线，检查允许修改范围。','未发现越界修改或删除。'),
 'native_render':('真实引擎画面已生成','原生 Compatibility 渲染能够加载当前候选并保存截图。','启动 Godot 原生渲染，读取实际视口像素并检查保存结果。','实际截图已保存；截图成功不等于视觉效果已获人审。'),
 'native-render':('真实引擎画面已生成','从正常入口加载城市，原生渲染并保留界面截图。','启动 Godot gl_compatibility 并保存运行时画面。','正常启动画面已保存；可读性仍待人审。'),
 'execution_health':('导入和验证运行正常','本轮命令成功退出且无运行时 SCRIPT ERROR。','检查导入、行为测试与截图命令的退出状态及日志。','本轮命令检查通过，原始日志可展开核对。'),
 'commands':('导入和验证运行正常','导入、行为检查和原生渲染均正常退出，无 SCRIPT ERROR。','核对每次执行的退出码、超时状态与错误日志。','本轮命令检查通过；预期负例文件错误与脚本错误分开。'),
 'import':('工程导入正常','Godot 能导入本工程且无脚本解析错误。','以 headless editor 执行资源导入，核对日志。','Godot 4.7.2 导入成功。')}
D={}
def rows(case,**kw):D[case]=kw
rows('racing-04',
 default_motorcycle=('默认是真实摩托车','主场景默认使用原摩托车对象、专用声音和有效镜头目标。','启动主场景，检查实际对象节点、engine_sound 路径和 View.target。','发现 motorcycle 模型节点、engine-motorcycle.ogg 和绑定的相机目标。'),
 moving_tab_rejected=('行驶中拒绝换车','行驶时按 Tab 不换车，并显示先停车提示。','实际输入驾驶后发送 Tab，比较活动车辆实例 ID 和提示文字。','原摩托车仍有效且实例未替换，出现 Stop first。'),
 motorcycle_drives=('摩托车可以实际行驶','1.5秒前进输入后真实物理车位移 >1.5 m。','发送原有前进 Input，测量 RigidBody3D 的位置变化。','1.5秒移动约7.364109 m。'),
 motorcycle_effects=('摩托车专用动作有效','侧倾和前叉旋转幅度 >0.02 rad，前轮旋转幅度 >0.1 rad。','实际驾驶与转向输入后读取摩托车、前叉和车轮旋转。','三项专用动作断言均通过；观感仍需试玩判断。'),
 stopped_tab_switch=('停车换车保持位置朝向','停车条件：速度 <0.5 m/s 且驱动状态 <0.08；换车位置偏差 <0.03 m，朝向点积 >0.999。','预设停车后发送 Tab，检查新车真实模型、物理位置和朝向。','切换为黄色卡车，位置和朝向均在测试容差内。','测试前将车速归零；此项没有覆盖自然制动到停车的全过程。'),
 camera_and_single_vehicle=('只有一辆活动车，镜头和HUD跟随','旧车释放，活动控制器数为1，镜头绑定新车；相机位置变化 <0.4 m。','在实际停车切换后查询场景树、旧实例有效性、View.target 和 HUD 文本。','旧摩托车已释放，只有1辆车，HUD显示 YELLOW TRUCK，镜头断言通过。','与停车换车共用预设静止状态。'),
 truck_drives=('黄色卡车仍可驾驶','1.5秒前进输入后真实物理车位移 >1.5 m。','切换到卡车后发送原前进 Input，测量车身实际物理位移。','1.5秒移动约7.364106 m。','驾驶前把卡车重置到原道路起点，便于单独验证驾驶。'),
 ten_repeated_switches=('连续10次换车不残留车辆','每次切换后保持姿态、仅1辆活动车，且相机目标有效。','反复预设停车并发送10次真实 Tab 输入，逐次检查状态。','10次切换全部通过，无双车和空相机目标。','每次切换前注入停车状态；不是10次完整驾驶—制动测试。'))
rows('racing-03',
 real_input_lookahead_direction=('镜头看向真实行驶前方','实际水平速度与前瞻偏移的点积 >1。','原前进 Input 驱动物理车，测量速度与镜头前瞻向量。','修复后点积约+29.216；修复前约−29.216。'),
 actual_input_drive=('调校后车辆仍能有效起步','2秒真实前进输入位移 >2 m。','实际 Input 加真实刚体模拟，读取起终点位置。','2秒位移约11.79 m，未靠极低速度实现稳定。'),
 brake_before_reverse=('S先制动再倒车','正驱动先减小，再进入负值倒车；最终驱动状态 <−0.3。','预设正向驱动状态，输入 S 并逐帧调用产品更新。','首次更新仍为正且减小，后续进入半强度倒车。','预设驱动状态以隔离制动逻辑。'),
 coast=('松油门平滑减速','驱动状态连续单调下降，测试终值在0.05与0.3之间。','预设驱动状态，松开输入，逐帧采样产品函数输出。','单调性和终值范围检查通过。','这是受控状态检查，不是覆盖所有地形的滑行测试。'),
 speed_sensitive_steering=('高速转向弱于低速','低速增益 >2.5，高速增益介于0.5与1.2。','注入低、高水平物理速度，比较产品转向增益。','低速灵活、高速降低的数值条件通过。','速度由测试预设，手感仍待人工。'),
 continuous_turns=('连续转向响应有界','60 Hz每步转向响应变化 <0.2 rad/s。','在预设高速下交替发送左右 Input，记录相邻帧变化。','最大步进变化约0.181 rad/s，低于阈值。','高速由测试预设；不代表所有连续弯道操作都已验证。'),
 parameter_effect=('Inspector参数实际生效','驱动力翻倍应使施加驱动翻倍；转向参数应改变真实增益。','修改导出参数并调用产品驱动和转向计算，对比前后结果。','参数影响与预期一致，误差断言 <0.01。','参数变化在隔离测试中进行，最终候选默认值未被测试值覆盖。'),
 camera=('加减速时镜头平滑过渡','近景 <10.1、远景 >18、前瞻 >3 m；第一帧缩放变化 <0.1并能平滑回近景。','注入速度阶跃，逐帧记录镜头位置、前瞻和回落趋势。','距离、首帧变化与回近景断言全部通过。','速度阶跃是受控测试；实际方向另由真实Input检查覆盖。'))
rows('racing-02',
 countdown_input_lock=('倒计时内锁定驾驶','开始前3秒车辆不离开出生点。','倒计时期间发送前进 Input，检查刚体冻结与位置。','车辆仍在出生点，输入未造成移动。'),
 countdown_go=('倒计时结束开启计时','3、2、1结束后释放驾驶并开始计时。','运行真实计时器，等待3秒后读取比赛状态。','控制释放且计时开始。'),
 missing_and_out_of_order=('漏点和乱序不推进','未过CP1先过终点或CP2，不应完成或推进。','让真实物理球体穿越对应 Area3D，读取进度。','两种违规顺序均被拒绝。','预设球体起始位置和速度；之后为真实碰撞穿越。'),
 reverse_checkpoint=('逆向检查点无效','反向穿过CP1不推进。','预设逆向接近状态，运行刚体穿过检测平面。','CP1逆向穿越被拒绝。','位置和速度由测试预设。'),
 physical_cp1=('正向检查点有效','正向穿越CP1应推进到下一检查点。','物理球体实际穿越CP1的 Area3D 和方向平面。','CP1进度正常推进。','测试预设接近位置与速度。'),
 skip_cp2=('不能跳过CP2','完成CP1后直接过CP3不推进。','实际球体穿越CP3，核对检查点索引。','跳过CP2被拒绝。','预设接近位置与速度。'),
 ordered_cp123=('按顺序完成三个检查点','按1→2→3正向通过后全部记录。','依次运行物理穿越，检查逐步进度。','三个检查点按顺序完成。','每次接近状态受控；完整连续驾驶另有整圈检查。'),
 reverse_finish=('逆向终点无效','完成检查点后反向终点不结束比赛。','实际球体逆向穿过终点检测平面。','比赛保持未完成。','预设接近位置与速度。'),
 correct_finish=('正确过线完成比赛','完成1→2→3后正向终点保存成绩。','实际正向物理穿越终点并读取计时结果。','比赛完成且保存了用时。','边界检查采用预设接近状态。'),
 final_timer_stops=('完赛后计时停止','完成后显示成绩不再增加。','完赛后继续运行，比较前后结果。','最终成绩保持不变。'),
 r_restart=('R重新开始全部状态','恢复出生姿态、零速度、倒计时和检查点状态。','发送实际 R 输入，对照重开前后状态。','位置、朝向、速度、计时与进度均重置。'),
 actual_input_lap=('实际输入连续跑完一圈','原输入驾驶按顺序完成全部检查点和终点。','测试驾驶器只发送驾驶Input，让原控制器和物理引擎运行。','连续驾驶119.74 m，约55.8模拟秒完赛，最大中心线误差1.90 m。'))
rows('platformer-01',
 required_inventory=('金币和特殊平台完整','保留14枚金币、3个下坠平台和3个砖块。','加载当前场景并按对象类型逐项计数。','实测14枚金币、3个平台、3个砖块。'),
 main_route_physics=('主路线从原出生点可达','从原出生点用原控制器通过全部主线路段，不依赖下坠平台。','发送移动和跳跃 Input，使用 CharacterBody3D 真实物理检查落点。','7段主线跳跃全部成功，沿途实际拾取7枚金币。'),
 branch_route_physics=('挑战支路可返回主线','经过3个下坠平台后可回接主线。','从分岔处连续输入跳跃，逐段检测真实落地。','8段支路跳跃全部成功并回到主线。','仅起点把角色放在分岔平台，后续连续使用原Input与物理。'),
 all_coins_reachable=('全部14枚金币能被拾取','主线与支路实际拾取ID并集包含全部14枚。','记录真实身体与金币触发器碰撞产生的拾取ID，跨两条测试路线去重。','拾取ID并集为14/14；不是仅统计场景中存在的金币。','支路使用一次起点位置预设。'),
 branch_bricks_breakable=('三个支路砖块可顶碎','每个砖块均能被原跳跃实际碰撞打碎并移除。','分别载入新场景，把角色放在砖下后发送跳跃，观察 BottomDetector 与碎裂结果。','3个砖块均由实际跳跃顶碎，效果结束后移除。','每块砖使用独立起点预设；不直接调用 explode。'))
rows('platformer-02',
 zero_coin_goal_rejected=('零金币不能通关','0枚进入终点应提示还差8枚，不能完成。','将角色放入真实终点 Area3D，等待 body-enter 事件。','提示 NEED 8 MORE COINS，保持未完成。','预设角色位置，不是从出生点走到终点。'),
 can_leave_locked_goal=('未达标仍可继续探索','被拒绝后仍能离开终点继续移动。','触发锁定终点后检查角色运动与离开行为。','没有错误冻结未完成的角色。','共用终点位置预设。'),
 coin_counts_once=('同一金币不重复计数','重复接触已收集金币不再加分。','使角色与同一真实金币区域重复接触，对比计数。','接触前后均为7枚，没有重复增加。','使用位置预设触发实际碰撞。'),
 seven_coin_goal_rejected=('差一枚时拒绝通关','7枚进入终点不能完成，提示还差1枚。','实际收集触发达到7枚后进入终点触发区。','提示 NEED 1 MORE COINS，保持未完成。','通过预设位置接触真实收集器；不是完整路线通关。'),
 eight_coin_goal_completes=('8枚金币后通关','达到8枚后进入终点，应完成一次并停止角色。','真实金币/终点触发后检查 completed 与 completion_count。','coins=8、completed=true、completion_count=1。','使用位置预设，先消耗砖块/平台用于后续重开验证。'),
 completion_is_idempotent=('重复进入不重复完成','同一关成功只计一次。','已成功后再次触发终点并比较完成次数。','完成次数仍为1。'),
 success_panel_visible=('成功面板和按钮完整可见','面板与按钮矩形完全包含于1280×720视口。','读取实际Control矩形与视口矩形做包容检查。','面板530×280位于(375,220)，按钮470×56位于(405,367)，完整可见。','成功状态由测试触发。'),
 restart_restores_world=('点击重开恢复整个世界','重载后金币数归零，14枚金币、3个平台、3砖块与角色恢复。','向可见产品按钮中心发送真实Viewport鼠标按下/释放，再检查新场景。','场景实例已更换，14枚金币及其他被消耗对象恢复。','重开前通过产品函数消耗砖块/平台；不是手工重置世界。'))
rows('platformer-03',
 coyote=('离台0.12秒内仍可起跳','离开平台0.12秒内可地面跳，过期后只剩空中跳。','用原角色实际走出台边，在不同延迟发送新跳跃输入。','0.116667秒输入仍保留空中跳；0.133333秒输入只消耗剩余空中跳。','测试专用平面和出生点；使用原角色与碰撞体。'),
 jump_buffer=('落地前0.15秒内缓存跳跃','耗尽二跳后，落地前0.15秒内新按键触发落地跳；更早输入过期。','实际输入耗尽两跳，在指定落地前时间再按一次，记录处理到落地间隔。','0.116667秒输入成功；0.183333秒输入过期；另测0.066667与0.2秒。','使用原角色与测试平面；按60 Hz离散测量。'),
 jump_limits=('不增加第三跳或长按自动跳','二跳上限不变；长按落地不重复触发；速度250/跳跃7保持。','连续按跳跃检查上升速度；持续长按直到落地，检查参数和状态。','第三跳未重置上升速度；长按1.666667秒不自动再跳；参数250/7。','测试平面与起点预设。'))
rows('platformer-04',
 runtime_visuals=('黄昏与危险平台真实生效','暖色天空/云层与斜纹下坠平台生效，原收集和下坠机制仍正常。','读取运行材质、数量与光照；截图后触发真实金币碰撞和平台碰撞。','14枚金币、3下坠平台、3个斜纹模型；金币HUD更新为1，平台真实下落。','截图之后把金币移到角色、把角色放到平台上，用于隔离机制检查。'),
 hud=('金币HUD留白与更新','保留原字体，1280×720下使用有留白的金币面板，计数正常更新。','读取运行Control矩形、字体、文本，并触发一次金币碰撞。','保留Lilita字体；深紫面板、暖金文字、28 px外边距；计数更新。','碰撞更新测试使用预设接触位置。'))
for ident in ['city-01-civic-square','city-02-road-stroke','city-03-save-safety','city-04-build-palette']:
 rows(ident,startup=('初始地图与余额正确','正常启动应保留示例城市及5860余额，不使用测试状态冒充初始状态。','直接加载主场景，对照官方122格地图和余额。','初始状态符合要求。'))
D['city-01-civic-square'].update({
 'startup':('扩建城市直接可见','直接启动加载扩建版，格子>122且余额5860。','启动正式主场景，统计GridMap和资金。','直接显示149格城市，余额5860。'),
 'original-cells':('原122格原样保留','既有格子的坐标、结构类型、朝向必须一致。','遍历官方地图和当前GridMap，逐格比较。','122个原格全部一致。'),
 'layout':('新社区紧凑且连通','新增区位于x3..8、z6..10；至少两种住宅、铺装、草地和高低树；入口接原路。','对新增格子做范围与类型检测，再遍历邻接关系和入口道路。','新增27格，27格全部连通，两种住宅及分层绿化齐全。'),
 'build-controls':('扩建后仍可正常编辑','选择、90度旋转、建造扣费、拆除与F3恢复示例城市有效。','发送实际Input触发产品建造方法，检查格子和余额变化。','Q/E、旋转、精确扣费、拆除通过；F3恢复122格。')})
D['city-02-road-stroke'].update({
 'startup':('保留原城并说明道路模式','起始122格/5860资金不变，拖动前可见道路模式。','直接启动后比较地图并读取模式提示。','122格和5860资金保持，ROAD MODE可见。'),
 'stroke-preview-commit':('拖动预览，松开一次提交','提交前不改地图/资金；重复格只计一次，转弯有预览。','发送真实鼠标按下、转弯、重复经过、松开事件，比较完整状态。','5个去重预览格；松开前零改动，提交后只扣125，余额5735。','固定1280×900视口与已稳定相机，以便鼠标投射到指定格。'),
 'stroke-cancel-conflict':('取消或冲突不破坏城市','Esc取消零变更；非道路占用使整段拒绝并显示原因。','发送Esc取消，再拖过已有住宅；对照格子与余额快照。','取消保持原状态；住宅冲突可见，整段拒绝。','固定视口和相机的真实鼠标测试。'),
 'single-build-controls':('住宅绿地保持单格建造','Q/E和右键旋转保留；住宅/草地仍单格放置且按原价收费。','发送选择/旋转和世界鼠标输入，检查结构类型、朝向与资金。','住宅与草地单格放置、模式切换、旋转与扣费通过。')})
D['city-03-save-safety'].update({
 'latest-save':('F2读到最后一次真实保存','连续两次不同状态保存后，读取第二次位置、类型、旋转与资金；绕过旧缓存。','真实ResourceSaver写入两次，特意保留第一次缓存后F2加载。','第一次5810、第二次5750；读取5750且整图状态精确一致。','独立user://测试目录；旧资源缓存刻意保留。'),
 'save-failure':('写入失败保留已有存档','临时文件写入失败应报错，城市、dirty状态及旧存档字节保持。','把临时目标设置为不可写的目录冲突，执行保存并比较状态和旧文件。','错误被报告，当前城市和原存档字节未改变。','只在隔离目录构造写入失败，不改用户存档。'),
 'failed-load-preserves':('缺失坏档不清空城市','不存在、坏字节、非法结构类型均拒绝加载且完整保留城市与余额。','在隔离目录依次构造3类负例，调用产品加载并比较状态。','3类失败均被捕获，地图和余额保持且有原因提示。','负例存档为测试预设；预期文件错误不等于脚本崩溃。'),
 'sample-reset':('F3安全确认后恢复示例城','有未保存修改时先确认；取消保持，确认恢复122格/5860且不覆盖用户档。','触发真实确认框，再触发其按钮pressed信号检查取消与确认分支。','提示、取消、确认均通过；官方城恢复，用户存档未变。','按钮使用真实Control的信号，未测试鼠标实际点中确认按钮。')})
D['city-04-build-palette'].update({
 'palette-content':('15种结构可辨认选择','显示15项原名称与价格，分道路/建筑/地面景观3组。','遍历UI按钮，核对结构资源、名称、原价和模型提示。','15项齐全、3组正确，提示关联真实模型文件。'),
 'gui-no-clickthrough':('点面板不会误建造','GUI点击只选择，不修改城市/余额；世界点击仍能建造。','逐个发送15次真实Viewport鼠标点击，再向世界空格点击。','15项均只改变选择；世界点击成功建造并扣费。'),
 'keyboard-preview-sync':('键盘、面板与模型同步','Q/E按原索引轮换，唯一高亮与3D预览一致。','输入15次下一项及上一项，核对当前索引、高亮和模型。','全部同步，索引顺序保留。'),
 'affordability-layout':('余额提示与小窗口布局','资金不足明确提示；在1280×900、1024×768下宽度≤30%视口。','暂设0余额再恢复，核对状态与价格颜色，并测量两种窗口Control矩形。','不足与恢复均刷新；面板宽260 px、两种尺寸均通过。','0余额仅注入隔离测试；正式起始余额仍5860。')})
rows('racing-01',
 project_loads=('修改后工程可运行','原资源正常加载，无脚本或资源错误。','独立副本中导入工程并加载主场景。','无资源或脚本错误。'),
 protected_gameplay=('只改路线与布景','受保护文件和GridMap外主场景节点、出生点、镜头保持原样。','逐文件哈希比较，并比较主场景GridMap数据以外文本。','受保护文件差异为0，GridMap以外保持一致。'),
 closed_track=('赛道是一条闭合环线','所有道路格形成唯一连通环，每个端口恰有一个匹配邻端口。','读取GridMap砖块和朝向，构建道路端口邻接图检查连通与度数。','闭环检查通过，没有断头、分支或孤立道路岛。'),
 required_geometry=('长直道与左右连续弯','至少连续3块普通直道，至少一对反号连续弯，并使用原终点外观砖。','从原出生前向遍历环线，统计直道连续长度、弯道符号和终点砖。','三项几何要求全部满足；终点砖要求在契约v2补充复验。'),
 spawn_and_decor=('出生点和布景位置合理','出生点在路上，道路不越地面；至少一个帐篷在环外，森林/帐篷不占道路格。','检查道路坐标、路线多边形及装饰占格，保留原生视角供人工复核。','几何与占格检查通过；森林是否遮挡驾驶视野仍待人工。'),
 physical_lap=('原控制器实际开完一圈','60 Hz、≤18000步、中心线偏差≤2.5 m，按顺序回到起点2 m内，无倒车/传送。','外部驾驶器仅发送原Input，原刚体完整通过路线，记录位置与输入轨迹。','3519步/58.65秒，行驶134.727 m；最大偏差1.993 m，回到起点0.355 m内。'))
# Frozen contract entries to concrete result checks. Different IDs are mapped explicitly.
MAP={
 'racing-04':{'default_motorcycle':['default_motorcycle','motorcycle_effects'],'stopped_switch':['stopped_tab_switch','camera_and_single_vehicle'],'moving_rejected':['moving_tab_rejected'],'repeat_and_drive':['motorcycle_drives','truck_drives','ten_repeated_switches','motorcycle_effects'],'preservation':['preservation']},
 'racing-03':{'preserve':['preservation'],'steering':['speed_sensitive_steering','continuous_turns','parameter_effect'],'drive_brake_coast':['actual_input_drive','brake_before_reverse','coast'],'camera':['camera','real_input_lookahead_direction']},
 'racing-02':{'preservation':['preservation'],'countdown':['countdown_input_lock','countdown_go'],'direction_and_sequence':['missing_and_out_of_order','reverse_checkpoint','physical_cp1','skip_cp2','ordered_cp123','reverse_finish','correct_finish','final_timer_stops','actual_input_lap'],'restart':['r_restart'],'hud_render':['native_render']},
 'platformer-01':{'source_preserved':['source_preserved'],'route_layout':['required_inventory','main_route_physics','branch_route_physics','all_coins_reachable'],'physical_routes':['main_route_physics','branch_route_physics','branch_bricks_breakable'],'native_render':['native_render']},
 'platformer-02':{'preservation':['preservation'],'goal_gate':['zero_coin_goal_rejected','can_leave_locked_goal','seven_coin_goal_rejected','eight_coin_goal_completes','completion_is_idempotent'],'coin_single_count':['coin_counts_once'],'restart':['restart_restores_world','success_panel_visible'],'native_render':['native_render','success_panel_visible']}}
CSTD={
 ('racing-04','default_motorcycle'):('真实摩托车默认接入','默认加载原摩托车场景，保留专用侧倾、前叉/车轮脚本与发动机音效。'),
 ('racing-04','stopped_switch'):('停车换车保持完整状态','速度 <0.5 m/s 且驱动状态 <0.08 才允许Tab切换；保持物理位置和朝向，仅1辆活动车，镜头目标有效。'),
 ('racing-04','moving_rejected'):('行驶时拒绝切换','速度 ≥0.5 m/s 或驱动仍活跃时拒绝切换，并显示先停车提示。'),
 ('racing-04','repeat_and_drive'):('两车可驾驶且反复切换稳定','两种车辆实际输入可移动；反复换车只有1辆活动车；摩托车专用动作有效。'),
 ('racing-03','preserve'):('只调整车辆与相机脚本','只改vehicle.gd与view.gd，原赛道、卡车、效果、输入保持。'),
 ('racing-03','steering'):('速度相关转向与参数','物理速度增大时转向增益降低；响应平滑有界；4个Inspector参数实际影响产品计算。'),
 ('racing-03','drive_brake_coast'):('起步、制动与滑行','2秒实际前进位移>2 m；S先减小正驱动再倒车；松油门指数平滑减速。'),
 ('racing-03','camera'):('镜头按实际速度平滑前瞻','高速拉远并前瞻，速度阶跃不立即跳变，减速平滑回近景。'),
 ('racing-02','countdown'):('倒计时与输入锁定','实际3秒倒计时锁定物理车与输入，GO后开始计时。'),
 ('racing-02','direction_and_sequence'):('方向与顺序决定成绩','实际车体正向通过CP1→2→3，再正向通过终点；漏点、乱序和逆向不得完赛。'),
 ('racing-02','restart'):('完整重新开始','R恢复出生物理姿态、速度、倒计时、计时和检查点状态。'),
 ('racing-02','hud_render'):('标记与计时画面可检查','原生截图呈现HUD与编号检查点；可读性仍待人工判断。'),
 ('platformer-01','route_layout'):('主支路线与原物体保留','保留14金币、3下坠平台、3砖块；主线从原出生到旗帜，不依赖下坠平台；支路回接。'),
 ('platformer-01','physical_routes'):('使用原物理验证路径','原CharacterBody3D/Input通过主线；支路真实物理跳跃，明确披露位置预设。'),
 ('platformer-02','goal_gate'):('8枚金币通关门槛','真实终点Area在0/7枚时拒绝，8枚完成一次，只有成功后冻结角色。'),
 ('platformer-02','coin_single_count'):('金币只计数一次','真实金币Area拾取一次，重复接触不重复计数。'),
 ('platformer-02','restart'):('产品按钮恢复场景','正式重开重载世界，恢复玩家、零计数、14金币、3下坠平台与3砖块。')}
SUM={
 'platformer-01':'保留原角色和素材，把关卡重排成逐级上升的主线与可回接的挑战支路。',
 'platformer-02':'为原旗帜增加8枚金币通关门槛、成功面板和完整重开流程。',
 'platformer-03':'加入离台宽限与落地前跳跃缓存，让边缘和落地跳跃更宽容。',
 'platformer-04':'把原关卡改为黄昏氛围，增强下坠平台识别和金币HUD对比度。',
 'city-01-civic-square':'在原喷泉南侧扩建27格社区休闲区，完整保留原122格城市。',
 'city-02-road-stroke':'新增道路拖拽预览、一次提交、取消和冲突保护，住宅仍单格建造。',
 'city-03-save-safety':'真实保存与读取最后版本，错误保留当前城市，重载官方地图前确认。',
 'city-04-build-palette':'把Q/E轮换扩展成15项分组选择面板，保留原建造规则。',
 'racing-01':'使用原赛道砖和布景重排林间练习闭环，由原车辆实际输入跑通一圈。',
 'racing-02':'新增倒计时、三个顺序检查点、方向检测、圈内计时与R重开。',
 'racing-03':'只改车辆与镜头脚本，加入速度相关转向、平滑制动和朝真实行进方向的前瞻。',
 'racing-04':'复用原摩托车与卡车，实现默认摩托车、停车Tab换车及镜头和HUD同步。'}
HUMAN={
 'platformer-01':['主线与支路是否一眼能辨认？','落点、节奏、风险与金币回报是否合理？','自由操作是否能顺利往返？'],
 'platformer-02':['目标、缺额与通关提示是否容易理解？','成功面板和重开按钮是否好用？','自由探索与收集手感是否合适？'],
 'platformer-03':['台边宽限和落地缓冲是否自然？','提示是否清晰？实体手柄操作是否正常？'],
 'platformer-04':['黄昏远近层次和前景识别是否清楚？','普通/下坠平台与落点边缘是否易辨认？'],
 'city-01-civic-square':['新增社区是否与喷泉空间协调？','入口、住宅朝向与人行铺装是否合理？'],
 'city-02-road-stroke':['转弯拖拽与预览是否易理解？','取消和冲突提示是否清楚？'],
 'city-03-save-safety':['成功/错误提示是否清晰且不挡建造？','F3确认流程是否容易理解和操作？'],
 'city-04-build-palette':['名称是否能对应模型？','不同窗口下城市主体与面板是否清晰？','鼠标与键盘交替选择是否顺手？'],
 'racing-01':['接缝与连续弯道是否好开，不必倒车脱困？','帐篷在环外，森林不遮住道路与跟随视角？','是否符合林间练习路线的感觉？'],
 'racing-02':['实际一圈的标记、计时和驾驶体验是否清楚？'],
 'racing-03':['低速与高速转向手感是否合适？','高速前方道路可见性与减速镜头是否自然？'],
 'racing-04':['摩托车手感与侧倾是否自然？','停车换车后的镜头是否连贯？','车型与拒绝换车提示是否清晰？']}
REQ={
 'racing-04': [('默认摩托车，保留专用动作与音效。',['default_motorcycle','motorcycle_effects']),('停车按Tab换车，保持位置、朝向、镜头和车型HUD。',['stopped_tab_switch','camera_and_single_vehicle']),('行驶中拒绝换车并提示先停车。',['moving_tab_rejected']),('两车均可驾驶，多次切换无幽灵车或失效镜头。',['motorcycle_drives','truck_drives','ten_repeated_switches'])],
 'racing-03':[('低速易转、高速平稳，参数可在Inspector调整。',['speed_sensitive_steering','continuous_turns','parameter_effect']),('保留先制动后倒车，松油门自然减速。',['brake_before_reverse','coast','actual_input_drive']),('高速能看见前路，减速镜头平滑回近景。',['camera','real_input_lookahead_direction'])],
 'racing-02':[('倒计时后才能起步并开始计时。',['countdown_input_lock','countdown_go']),('必须按顺序、正确方向通过检查点再完成。',['missing_and_out_of_order','reverse_checkpoint','ordered_cp123','reverse_finish','correct_finish','actual_input_lap']),('成绩停止更新，R能完整重开。',['final_timer_stops','r_restart']),('看得清检查点与计时HUD。',['native_render'])],
 'racing-01':[('从黄色卡车出生点能连续开完一圈，不用倒车脱困。',['closed_track','physical_lap']),('至少三块连续直道、先左后右连续弯，并用终点外观砖。',['required_geometry']),('帐篷在环外，森林不覆盖道路或遮挡驾驶视角。',['spawn_and_decor']),('只改路线和布景，保留车辆、输入、音效与镜头。',['protected_gameplay'])],
 'platformer-01':[('主线从原出生点逐级通向旗帜。',['main_route_physics']),('挑战支路包含特殊平台和奖励，并能回主线。',['branch_route_physics','branch_bricks_breakable']),('保留金币和特殊物体，使金币可以收集。',['required_inventory','all_coins_reachable'])],
 'platformer-02':[('金币不足不能通关，显示缺额且可以继续探索。',['zero_coin_goal_rejected','seven_coin_goal_rejected','can_leave_locked_goal']),('达到8枚后在旗帜通关，一枚金币和一次成功不重复计数。',['coin_counts_once','eight_coin_goal_completes','completion_is_idempotent']),('成功画面可读，点击重开恢复世界。',['success_panel_visible','restart_restores_world'])],
 'platformer-03':[('增加离台宽限和落地前按键缓存。',['coyote','jump_buffer']),('保持正常二段跳，不出现第三跳或长按自动跳。',['jump_limits']),('保留原关卡、参数、镜头与手柄映射，新增清楚提示。',['preservation','native_render'])],
 'platformer-04':[('原关卡改为黄昏层次，强化下坠平台和HUD识别。',['runtime_visuals','hud','native_render']),('不改变关卡布局、碰撞与原有玩法。',['preservation','runtime_visuals'])],
 'city-01-civic-square':[('围绕喷泉在空地扩建有住宅、分层绿化与人行铺装的社区。',['layout','startup']),('保留原有街区，新增入口接原路。',['original-cells','layout','preservation-files']),('进入即看到扩建，仍能继续正常建造。',['startup','build-controls'])],
 'city-02-road-stroke':[('按住拖动预览道路，松开一次提交，重复格只收费一次。',['stroke-preview-commit']),('Esc取消不改资金地图，不可无提示覆盖建筑。',['stroke-cancel-conflict']),('明确道路模式，保留建筑绿地单格建造。',['startup','single-build-controls'])],
 'city-03-save-safety':[('连续保存后读取最后真实状态，并给出清晰提示。',['latest-save']),('缺失、损坏、写读失败均保护当前城市和存档。',['save-failure','failed-load-preserves']),('F3独立恢复官方示例，丢未存修改前提醒。',['sample-reset','preservation-files'])],
 'city-04-build-palette':[('面板按类别展示可选结构、名称和价格。',['palette-content']),('鼠标选项与Q/E同步，点UI不误建造。',['gui-no-clickthrough','keyboard-preview-sync']),('显示余额是否够用，保持城市主体清楚。',['affordability-layout','native-render'])]}
NAMES={'vehicle-motorcycle':'摩托车','vehicle-truck-yellow':'黄色卡车','vehicle':'车辆对象','view':'跟随相机','engine-motorcycle':'摩托车发动机声','engine':'发动机声','player':'玩家角色','character':'角色外观','platform':'平台','platform_falling':'下坠平台','platform_medium':'中型平台','platform_grass_large_round':'大型圆草地平台','coin':'金币','flag':'旗帜','brick':'可顶碎砖块','cloud':'云朵','skybox':'天空背景','colormap':'模型配色','particle':'粒子','lilita_one_regular':'Lilita 字体','main':'主场景','mesh-library':'道路积木库','track-straight':'直道','track-corner':'弯道','track-finish':'终点外观砖','decoration-forest':'森林布景','decoration-tents':'帐篷布景','decoration-empty':'空地布景','map':'官方示例地图','selector':'选中标记','instructions':'操作提示','jump':'跳跃音效','land':'落地音效','skid':'轮胎摩擦声','smoke':'烟雾','pavement-fountain':'喷泉铺装','pavement':'人行铺装','grass':'草地','grass-trees':'低树绿地','grass-trees-tall':'高树绿地','road-straight':'直路','road-straight-lightposts':'带路灯直路','road-corner':'弯路','road-split':'岔路','road-intersection':'十字路','building-garage':'车库','toggle':'切换音效','placement-a':'放置音效'}
for letter in 'abcd':NAMES['building-small-'+letter]='住宅 '+letter.upper()
TYPES={'.tscn':'预配置场景/对象','.tres':'资源配置','.res':'资源数据','.glb':'3D模型','.gd':'控制脚本','.png':'图片素材','.ogg':'音频','.ttf':'字体'}
FILE_DESC={
 'scripts/view.gd':'调整相机或输入边界；具体改动见代码差异。','scripts/builder.gd':'实现本任务的城市编辑行为与界面反馈。','scripts/hud.gd':'实现目标、控制说明或成功面板等界面。','scripts/player.gd':'增加离台宽限和落地前输入缓存，保留原二跳。','scripts/vehicle.gd':'调整车辆驱动行为或接入比赛输入锁定。','scripts/vehicle_switcher.gd':'新增默认摩托车、停车换车、HUD及旧车释放逻辑。','scripts/race_manager.gd':'新增倒计时、检查点进度、计时和重开状态。','scripts/checkpoint.gd':'新增真实车辆Area和方向穿越检测。','scripts/race_hud.gd':'呈现倒计时、进度与完赛信息。','scenes/main.tscn':'修改本任务场景布局、节点引用或视觉配置。','scripts/main.gd':'接入本任务通关逻辑或视觉HUD；查看差异核对。','sample map/civic-square.tres':'单独保存扩建版城市，不覆盖官方示例。','scenes/main-environment.tres':'新增黄昏天空、光照和环境颜色。','objects/cloud.tscn':'把原云层调整为暖色。'}

def changed(p):
 data=read(p/'changed-files.json',{})
 if isinstance(data,list):return [x['path'] for x in data]
 data=data.get('changed',{})
 return list(data) if isinstance(data,dict) else [x['path'] for x in data]

def history_for(ident,p):
 h=[]
 def add(kind,title,description,result,files):
  evidence=[ev(p/f,l) for f,l in files if (p/f).is_file()]
  h.append(dict(id='event-'+str(len(h)+1),kind={'product_fix':'repair','checker_fix':'checker','criteria_change':'contract_amendment','execution_error':'failure','generation':'execution','baseline':'input'}.get(kind,kind),title=title,description=description,result=result,evidence=evidence))
 if ident=='racing-03':
  add('execution_error','早期脚本解析错误','导入日志记录新增函数混用缩进；这属于代码加载错误，不是驾驶玩法失败。','修正缩进后重新导入；不将命令数量当作生成轮数。',[('evidence/final/import.log','早期导入日志'),('evidence/final/import-v2.log','重新导入日志')])
  add('failure','交叉审查发现镜头前瞻反向','实际前进速度为正，但旧镜头向后偏移；新增真实Input方向断言复现。','速度与前瞻点积约−29.216，方向断言失败。',[('evidence/final/behavior-direction-before.json','修正前实测'),('evidence/final/view-before-direction-fix.gd.txt','修正前相机脚本')])
  add('product_fix','改用实际水平行驶方向','将原朝向符号计算替换为实际水平速度方向，并保留新的方向断言。','最终完整行为验证通过；点积约+29.216。仅保存旧局部源码，没有可试玩的完整旧候选。',[('project/scripts/view.gd','最终相机脚本'),('verification/behavior.gd','最终校验器'),('evidence/final/behavior.json','修正后实测'),('evidence/final/scene-moving.png','真实前进120帧后画面')])
 elif ident=='racing-01':
  add('baseline','初始工程未满足目标','先检查原路线与需求差距，保留初始画面与静态验证。','初始验证有未满足项；没有将输入准备状态当成候选结果。',[('evidence/baseline-verification-v2/result.json','初始验证')])
  add('generation','重排道路和布景','coding agent 修改GridMap数据，生成林间练习环线，保留原玩法。','布局候选为 layout-v1。',[('evidence/layout-v1/candidate-data.json','布局输出'),('evidence/layout-v1/decision.json','布局说明')])
  add('criteria_change','契约v2补上终点外观砖检查','审查发现v1遗漏原需求中的终点砖，增加检查后重新验证已有候选；没有降低阈值。','v2并非在layout-v1前冻结；页面明确展示这一变更。',[('contract/acceptance-v1.json','契约v1'),('contract/acceptance.json','契约v2')])
  add('checker_fix','修正测试驾驶器路点判断','早期驾驶器路点识别有缺陷，修正的是外部测试工具，候选路线没有因此重排。','最终只用Input完成3519物理步，6项检查通过。',[('verification/driver-development/dev001/result.json','驾驶器早期结果'),('verification/driver-development/dev002/result.json','驾驶器后续记录'),('evidence/final-verification-v2/lap.json','最终实测'),('evidence/final-verification-v2/result.json','最终v2验证')])
 elif ident=='platformer-01':
  add('product_fix','修正支路碰撞与金币落点','原下坠平台被邻岛碰撞提前触发，移开重叠后继续测试；随后调整遮挡测试落点的砖块。','最终两条路线及14枚金币可达性通过；没有完整保存每次旧工程。',[('evidence/behavior-01/run.log','首次失败日志'),('evidence/behavior-02/checks.json','中间行为结果'),('evidence/final/result.json','最终结果')])
 elif ident=='platformer-02':
  add('product_fix','修正成功面板出屏','原居中锚点叠加正偏移导致面板裁切；主agent调整为半宽半高负偏移。','新增真实按钮点击和矩形包容检查后通过。',[('evidence/root-ui-failure/hud-before.gd','修正前HUD'),('evidence/root-ui-failure/result-before.json','修正前记录'),('evidence/root-ui-fix/checks.json','修正后实测'),('project/scripts/hud.gd','最终HUD')])
 elif ident=='platformer-03':
  add('checker_fix','校准跳跃边界测试计时','原测试重复计入按键处理帧，修正测试计时后记录实际输入到落地的间隔。','离台与落地缓冲边界验证通过；这是校验器修正记录。',[('README.md','计时修正说明'),('evidence/final/result.json','最终边界结果')])
 elif ident=='racing-02':
  add('checker_fix','修正触发器测试等待时序','早期fixture等待时序导致测试失败，修正测试等待后重新运行。','触发器行为通过；不将此归为赛道玩法失败。',[('evidence/final/behavior-v1.json','早期行为记录'),('evidence/final/behavior.json','最终行为记录')])
  add('product_fix','缩小并抬高起终点标签','交叉审查发现标签过大，缩为原1/3并抬高3 m以改善视野。','重新导入、运行行为检查和原生渲染通过；整圈逻辑未变。',[('README.md','审查修正说明'),('evidence/final/scene.png','最终画面')])
 else:
  pass # No evidence-linked repair event is better than an invented timeline.
 return h
def make(ident,p):
 t=read(p/'task.json');s=read(p/'source.json');m=read(p/'manifest.json');co=read(p/'contract/acceptance.json')
 if t['base_id']=='city-builder':
  s=dict(s)
  s['title']=s['project_name'];s['repository']=s['repo']
  s['license']={'code':next(x['license'] for x in s['licenses'] if x['scope']=='code / project'),'assets':next(x['license'] for x in s['licenses'] if '3D models' in x['scope'])+'；字体 '+next(x['license'] for x in s['licenses'] if 'font' in x['scope'])}
  s['version']={'validated_godot':s['validated_engine_version'].removeprefix('Godot '),'declared_godot':'4.6','renderer_declared':'Forward Plus','physics':'工程未单独声明物理后端；本任务主要验证网格编辑与资源读写'}
 initial=t['initial_state']
 if isinstance(initial,list):initial=' '.join(initial)
 if isinstance(initial,dict):
  initial=('任务从已加载的官方示例城市开始：资源 '+initial['resource']+'，共'+str(initial['occupied_cells'])+'个已占格，资金'+str(initial['cash'])+'，喷泉位于网格(5,0,4)。上游直接启动原本是空地图；输入准备通过加载官方示例获得这里的小镇，尚未实现本任务需求。已有单格建造、拆除、90度旋转、相机操作、Q/E选择及F1/F2/F3存读档能力。输入基线仅补了鼠标射线未命中建造平面时的空值保护。')
  initial+=' '+{'city-01-civic-square':'喷泉旁尚未扩建社区休闲区。','city-02-road-stroke':'原工具一次点击只放一个结构，没有道路拖拽预览与整段取消。','city-03-save-safety':'原存读档还缺少本任务要求的失败保护、最新保存校验与未保存修改确认。','city-04-build-palette':'当前通过Q/E逐项轮换，尚无带名称、价格和分组的建筑选择面板。'}[ident]
 assert isinstance(initial,str), (ident,'initial_state must be text')
 rp=p/('evidence/final-verification-v2/result.json' if ident=='racing-01' else 'evidence/final/result.json');res=read(rp)
 category=t['base_id']; base=INPUTS/'bases'/category/'project'
 raw=res['checks'];raw=[{'id':k,'pass':v} for k,v in raw.items()] if isinstance(raw,dict) else raw
 checks=[]
 for item in raw:
  ci=item['id'];ex=D.get(ident,{}).get(ci,COMMON.get(ci))
  if ex is None:raise ValueError((ident,ci,'missing Chinese check'))
  checker=p/'verification'/('test.gd' if ident.startswith('city') else 'behavior.gd')
  if ci in ['preservation','source_preserved','preservation-files']:checker=p/'verification/preservation.py'
  if 'render' in ci:checker=p/'verification/render.gd'
  if ci=='physical_lap':checker=p/'verification/drive_lap.gd'
  if ident=='racing-01' and ci!='physical_lap':checker=p/'verification/check_racing.py'
  if ci=='branch_bricks_breakable':checker=p/'verification/bricks.gd'
  evidence=[ev(rp,'最终检查原始记录')]
  if checker.exists():evidence.append(ev(checker,'实际校验器代码'))
  for f in ['evidence/final/behavior.json','evidence/final-verification-v2/lap.json']:
   if (p/f).exists():evidence.append(ev(p/f,'行为与测量细节'))
  checks.append({'id':ci,'title':ex[0],'standard':ex[1],'method':ex[2],'actual':ex[3],'status':'pass' if item.get('pass') is True else 'fail' if item.get('pass') is False else 'unknown','fixture':ex[4] if len(ex)>4 else None,'evidence':evidence,'criterion_ids':[]})
 criteria=[]
 for c in co.get('hard_checks',co.get('objective_checks',co.get('checks',[]))):
  cid=c['id'];ids=MAP.get(ident,{}).get(cid,[cid] if cid in {x['id'] for x in checks} else [])
  x=next((x for x in checks if x['id'] in ids),None)
  st=CSTD.get((ident,cid),(x['title'],x['standard']) if x else (cid,'该标准尚未确认中文映射，请查原始契约。'))
  criteria.append(dict(id=cid,title=st[0],standard=st[1],source='原始任务与保留条件 → Codex agent 编写验收契约；具体阈值为契约/检查器的工程解释。',check_ids=ids,evidence_url=url(p/'contract/acceptance.json')))
  for x in checks:
   if x['id'] in ids:x['criterion_ids'].append(cid)
 assets=[]
 for path in t.get('available_assets',[]):
  ap=base/path
  if not ap.exists():raise ValueError(('missing asset',ap))
  typ=TYPES.get(ap.suffix,'输入资源');name=NAMES.get(ap.stem,ap.stem)
  role={'3D模型':'原工程随附外观，可供本任务复用。','控制脚本':'原工程行为或相机逻辑，是任务输入的一部分。','预配置场景/对象':'组合已有模型、控制器或碰撞组件。','音频':'原工程音效。','图片素材':'原有界面、纹理或粒子图片。','字体':'原界面字体与字体许可。'}.get(typ,'原有结构、地图或材质资源。')
  assets.append(dict(name=name,path=path,type=typ,role=role+' 声明可用；不把清单本身当作实际调用证据。',url=url(ap),preview=url(ap) if ap.suffix=='.png' else None))
 cfiles=changed(p) if ident!='racing-01' else ['scenes/main.tscn']
 changes=[dict(path=f,kind='modified' if (base/f).exists() else 'added',description=FILE_DESC.get(f,'本任务新增/修改的游戏材质或资源配置。'),url=url(p/'project'/f)) for f in cfiles if (p/'project'/f).exists()]

 for f in changes:
  if f['path']=='scripts/builder.gd':f['description']=SUM[ident]
  if ident=='racing-04' and f['path']=='scenes/main.tscn':f['description']='默认实例改为原摩托车场景，挂接换车控制器；原GridMap保持。'
  if ident=='racing-04' and f['path']=='scripts/view.gd':f['description']='提供新车镜头目标重新绑定，延续平滑跟随。'
  if ident=='racing-03' and f['path']=='scripts/vehicle.gd':f['description']='导出驱动力100、低/高速转向3.4/0.95、响应6；加入速度相关转向、制动与松油门平滑衰减。'
  if ident=='racing-03' and f['path']=='scripts/view.gd':f['description']='镜头按速度从近景10平滑拉远到19，沿实际水平行驶方向前瞻最多3.5米。'
  if ident=='racing-01':f['description']='只改GridMap道路和装饰布局，组成含三连直道、连续反向弯和终点砖的林间闭环。'
  if ident=='platformer-01':f['description']='移动平台、金币、砖块和布景，构成不依赖下坠平台的主线与可回接挑战支路。'
 # Attach verifier files separately from product changes; UI can display this optional field.
 checkers=[dict(path=str(f.relative_to(p)),url=url(f),description='用于验证候选的测试代码，不属于新增游戏功能。') for f in (p/'verification').glob('*') if f.suffix in ['.gd','.py']]
 media=[]
 mediafiles=[p/'evidence/layout-v1/overview.png',p/'evidence/layout-v1/driver-view.png'] if ident=='racing-01' else sorted((p/'evidence/final').glob('*.png'),key=lambda x:(x.name!='scene.png',x.name))
 for f in mediafiles:
  cam='原游戏相机';desc='实际 Godot 原生渲染截图；静态画面不证明完整操作过程。'
  if 'overview' in f.name or 'remote' in f.name or (ident=='platformer-01' and f.name=='scene.png'):cam='外置审查相机';desc+=' 此视角用于审查，未修改产品相机。'
  if ident=='platformer-02' and f.name in ['scene.png','success.png']:desc+=' 成功画面由预设位置/收集测试触发。'
  if f.name=='scene-moving.png':desc+=' 使用真实前进Input运行120物理帧后捕获。'
  media.append(dict(label={'scene.png':'最终效果','scene-default.png':'正常开局','overview.png':'全景审查','remote.png':'远端审查','scene-moving.png':'实际驾驶画面','driver-view.png':'驾驶视角','success.png':'成功状态'}.get(f.name,f.stem),url=url(f),kind='image',camera=cam,description=desc))
 baselinep=INPUTS/t['preview']
 if ident=='racing-01':baselinep=p/'evidence/baseline/driver-view.png'
 limits=res.get('limitations',[])
 if ident=='platformer-01':limits=['支路仅在开始时预设分岔位置，其余连续原Input与物理；砖块分别预设起点。','固定输入路线仅证明可行，不覆盖所有操作水平。','全景为外置审查相机，原游戏相机另有截图；可读性与手感待人审。']
 if ident=='platformer-02':limits=['行为测试预设角色位置接触真实Area；没有从出生点完整收集通关。','重开前预设消耗砖块与平台，再用真实鼠标点击可见按钮。','自由探索、提示理解和操作手感待人工。']
 if ident=='racing-01':limits=['一次有界的Input驾驶通过，不能证明所有速度和玩家水平均可通过。','装饰物没有碰撞体；视觉遮挡、风格与接缝手感仍需人工确认。','契约v2是补充终点外观砖检查后形成，已有候选已在v2下重新验证。']
 commands=[]
 for n,c in enumerate(res.get('commands',m.get('attempts',[]))):
  if isinstance(c,list):c={'command':c}
  if not isinstance(c,dict):continue
  command=c.get('command')
  if not command:continue
  if isinstance(command,list):command=shlex.join(map(str,command))
  desc='执行已保存的验证命令；原始路径和参数保留用于核对。'
  if '--import' in command:desc='导入游戏工程资源并检查脚本能否加载。'
  elif '--headless' in command and '--script' in command:desc='运行无窗口行为校验脚本，检查真实游戏状态、输入和物理结果。'
  elif c.get('name')=='render' or 'render.gd' in command or 'capture_views.gd' in command:desc='启动真实原生渲染，保存候选画面。'
  elif '--script' in command:desc='运行外部检查脚本，读取真实行为和物理结果。'
  elif '--rendering-method' in command:desc='使用指定渲染后端启动工程；具体产出以本条日志为准。'
  commands.append(dict(label='运行记录 '+str(n+1),command=command,exit_code=c.get('exit_code',c.get('returncode')),description=desc))
 actors=[dict(role='执行 agent',name='Codex coding agents',model=None,description='修改场景、脚本与资源配置，交付可运行工程。具体历史模型 ID、原始 prompt/response 未记录。'),dict(role='规则设计者',name='Codex agents',model=None,description='依据任务与保留条件编写验收契约和数值解释；没有调用独立 reward model。'),dict(role='程序验证器',name='Godot + Python / GDScript',model=None,description='运行输入、碰撞、场景及哈希检查，生成检查结果和证据。不是验证大模型。'),dict(role='交叉审查',name='主 Codex agent',model=None,description='核对工程、检查器、截图与证据；不计为人工审阅。'),dict(role='人工审阅',name='用户',model=None,description='试玩并判断手感、可读性与视觉质量；尚未提交的决定保持待审阅。')]
 ver=s.get('version',{})
 env=[{'label':'实际验证引擎','value':'Godot '+ver.get('validated_godot','4.7.2')},{'label':'实际渲染','value':'原生 gl_compatibility（Compatibility）'},{'label':'物理后端（工程配置）','value':ver.get('physics','原工程配置；见 source.json')},{'label':'上游声明','value':'Godot '+ver.get('declared_godot','未记录')+' / '+ver.get('renderer_declared','未记录')},{'label':'主场景','value':s.get('main_scene','res://scenes/main.tscn')},{'label':'运行位置','value':'本机 Godot；试玩创建独立运行副本与任务存档目录'},{'label':'行为测试参数','value':'固定60 Hz（出现 --fixed-fps 60 的运行）；其他参数见各条命令'}]
 for role in actors:
  role['model']='未记录' if 'agent' in role['role'] or role['role'] in ['规则设计者','交叉审查'] else '不适用'
 review=read(p/'human-review.json',m.get('human_review'))
 contract_hash=res.get('contract_sha256',m.get('contract_sha256'))
 return dict(id=ident,title=t['title'],category=category,category_label={'platformer':'平台跳跃','city-builder':'城市建造','racing':'赛车'}[category],summary=SUM[ident],query=t['query'],initial_state=initial,requirements=[dict(id='R-'+str(i+1).zfill(2),text=txt,source='原始任务需求；中文拆分与检查关联为2026-09-20后补展示说明。',check_ids=ids) for i,(txt,ids) in enumerate(REQ[ident])],preservation=t['required_preservation'],assets=assets,source=dict(name=s.get('title','原工程'),url=s.get('repository'),license='代码 '+s.get('license',{}).get('code','未记录')+' / 素材 '+s.get('license',{}).get('assets','未记录'),commit=s.get('commit')),environment=env,actors=actors,output=dict(summary=SUM[ident],changes=changes,notes=['输出是可运行的游戏工程与代码/场景修改；没有把截图当作模型生成的游戏。','未保存完整模型原始调用；本页过程解读是基于已有产物与证据的后补中文说明。'],checkers=checkers),criteria=criteria,checks=checks,history=history_for(ident,p),media=media,baseline=dict(url=url(baselinep),label='输入工程实际初始画面'),limitations=limits,human_checks=HUMAN[ident],review=review,hard_pass=res.get('hard_pass',all(x['status']=='pass' for x in checks)),engine_reward=res.get('engine_reward'),contract_hash=contract_hash,candidate_hash=None,links=[ev(p/'task.json','原始任务'),ev(p/'source.json','工程来源与许可证'),ev(p/'contract/acceptance.json','冻结契约'),ev(rp,'最终验证'),ev(p/'README.md','任务说明'),ev(p/'trajectory.jsonl','已保存轨迹')],record_notes=['具体模型ID、完整prompt/response、每次完整候选快照未采集。','时间线只展示有证据的事件；命令运行次数不等于模型生成轮数。','需求→检查的关联表示相关验证，不代表视觉与手感要求已自动全面覆盖。','中文过程解释为2026-09-20后补展示说明；原始代码、执行命令和日志保留原文。'],commands=commands,counts=dict(checks=len(checks),passed=sum(x['status']=='pass' for x in checks)),candidate_label='最终候选',history_complete=False,reward_formula=('契约规定：全部自动硬性检查通过才记1，否则记0。人工尚未评判，组合奖励保持空值。' if co.get('reward') else '原契约未记录统一聚合公式；最终结果记录 engine_reward=1，所有自动硬性检查通过。人工与组合奖励保持空值。'))

def main():
 ids=['platformer-'+f'{n:02}' for n in range(1,5)]+['city-01-civic-square','city-02-road-stroke','city-03-save-safety','city-04-build-palette']+['racing-'+f'{n:02}' for n in range(1,5)]
 cases=[make(ident,RACE if ident=='racing-01' else BATCH/'cases'/ident) for ident in ids]
 allurls=[]
 def visit(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if isinstance(v,str) and v.startswith('/files/'):allurls.append(v)
    else:visit(v)
  elif isinstance(x,list):
   for v in x:visit(v)
 visit(cases)
 for u in allurls:
  _,_,key,path=u.split('/',3);target={'batch':BATCH,'racing01':RACE,'inputs':INPUTS}[key]/unquote(path)
  assert target.is_file(),(u,target)
 for c in cases:
  assert isinstance(c['initial_state'],str) and c['initial_state']
  assert all(isinstance(c['source'][k],str) and c['source'][k] for k in ['name','url','license'])
  ids={x['id'] for x in c['checks']}
  assert all(set(x['check_ids'])<=ids for x in c['requirements']+c['criteria'])
 assert len(cases)==12 and all(sum(c['category']==cat for c in cases)==4 for cat in ['platformer','city-builder','racing'])
 data=dict(cases=cases,updated_at='2026-09-20',adapter_notes='只读适配12个已存在任务。中文解释为展示补充；不生成历史调用、人工决定或完整旧候选。')
 (HERE/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(cases=len(cases),checks=sum(c['counts']['checks'] for c in cases),local_links_verified=len(set(allurls)),bytes=(HERE/'data.json').stat().st_size),ensure_ascii=False))
if __name__=='__main__':main()

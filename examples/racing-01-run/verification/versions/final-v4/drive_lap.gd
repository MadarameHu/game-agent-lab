extends SceneTree
# External test: all writes to the product are Input actions only.
const MAX_STEPS=18000
const MAX_DEVIATION=2.5
const RETURN_RADIUS=2.0
const SETTLE_STEPS=60
var scene
var car
var sphere
var route=[]
var output_dir=""
var telemetry
var step=0
var next_index=1
var start_position=Vector3.ZERO
var previous_position=Vector3.ZERO
var traveled=0.0
var max_deviation=0.0
var max_y=0.0
var off_ground_steps=0
var finished=false
var started_usec=0
var lookahead=1.8
var throttle=0.24
var steer=0.0
func vec(p):return [p.x,p.y,p.z]
func xz(p):return Vector2(p.x,p.z)
func _initialize():call_deferred("setup")
func setup():
 var args=OS.get_cmdline_user_args()
 var data=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
 output_dir=args[1]
 for p in data.points:route.append(Vector3(p[0],0,p[1]))
 scene=load("res://scenes/main.tscn").instantiate();root.add_child(scene)
 car=scene.get_node("Vehicle");sphere=car.get_node("Sphere")
 start_position=sphere.global_position;previous_position=start_position
 telemetry=FileAccess.open(output_dir+"/telemetry.jsonl",FileAccess.WRITE)
 started_usec=Time.get_ticks_usec()
 for action in ["forward","back","left","right"]:Input.action_release(action)
func segment_distance(p,a,b):
 return xz(p).distance_to(Geometry2D.get_closest_point_to_segment(xz(p),xz(a),xz(b)))
func finish(reason,passed):
 if finished:return
 finished=true
 for action in ["forward","back","left","right"]:Input.action_release(action)
 if telemetry:telemetry.close()
 var result={"status":reason,"passed":passed,"driver":"input-pure-pursuit-v3","physics_steps":step,"physics_hz":Engine.physics_ticks_per_second,"simulation_seconds":float(step)/60.0,"wall_seconds":float(Time.get_ticks_usec()-started_usec)/1000000.0,"waypoints_total":route.size(),"waypoints_completed":next_index,"physical_start":vec(start_position),"physical_end":vec(sphere.global_position),"return_distance_xz":xz(sphere.global_position).distance_to(xz(start_position)),"distance_traveled_m":traveled,"max_local_centerline_distance_m":max_deviation,"max_sphere_y":max_y,"reverse_action_used":false,"parameters":{"lookahead_m":lookahead,"forward_strength":throttle,"waypoint_progress":"sequential perpendicular gates within current local segment error bound","settle_steps_included":SETTLE_STEPS},"criteria":{"max_steps":MAX_STEPS,"max_centerline_distance_m":MAX_DEVIATION,"return_radius_m":RETURN_RADIUS},"note":"Only Input.action_press/release used. Stock controller and rigid body remain unmodified. A driver failure alone does not prove human undrivability."}
 var f=FileAccess.open(output_dir+"/lap.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 print("LAP_RESULT "+JSON.stringify(result))
 scene.queue_free();quit(0 if passed else 2)
func _physics_process(_delta):
 if scene==null or finished:return false
 step+=1
 var position=sphere.global_position
 var velocity=sphere.linear_velocity
 var ground=car.raycast.is_colliding()
 var moved=xz(position).distance_to(xz(previous_position));traveled+=moved;previous_position=position
 max_y=maxf(max_y,position.y)
 if step>SETTLE_STEPS:
  if not ground:off_ground_steps+=1
  else:off_ground_steps=0
 var local_distance=segment_distance(position,route[maxi(next_index-1,0)],route[mini(next_index,route.size()-1)])
 if step>SETTLE_STEPS:max_deviation=maxf(max_deviation,local_distance)
 var heading=car.get_node("Container").global_basis.z
 telemetry.store_line(JSON.stringify({"step":step,"position":vec(position),"velocity":vec(velocity),"speed":xz(velocity).length(),"heading":vec(heading),"ground":ground,"next_waypoint":next_index,"local_centerline_distance":local_distance,"traveled":traveled,"input":{"forward":Input.get_action_strength("forward"),"left":Input.get_action_strength("left"),"right":Input.get_action_strength("right"),"back":Input.get_action_strength("back")},"input_timing":"actions applied during previous physics tick; observation before next controller update"}))
 if step>=MAX_STEPS:finish("driver_budget_exhausted",false);return false
 if step<=SETTLE_STEPS:return false
 if position.y < -0.25 or position.y > 1.25 or off_ground_steps>10:finish("vehicle_left_ground_band",false);return false
 if moved>1.0:finish("unexpected_physical_discontinuity",false);return false
 if local_distance>MAX_DEVIATION:finish("local_centerline_limit_exceeded",false);return false
 var gate_tangent=xz(route[mini(next_index+1,route.size()-1)])-xz(route[maxi(next_index-1,0)])
 var gate_crossed=(xz(position)-xz(route[next_index])).dot(gate_tangent)>=0.0
 if ground and gate_crossed:
  next_index+=1
  if next_index>=route.size():
   if xz(position).distance_to(xz(start_position))<=RETURN_RADIUS:finish("stock_physics_lap_pass",true)
   else:finish("ordered_route_done_but_not_at_start",false)
   return false
 # Fixed local lookahead, never snap to a global nearest route point.
 var target_index=next_index
 var ahead=xz(position).distance_to(xz(route[next_index]))
 while target_index+1<route.size() and ahead<lookahead:
  ahead+=xz(route[target_index+1]).distance_to(xz(route[target_index]));target_index+=1
 var target=route[target_index]-position;target.y=0
 var angle=atan2(heading.z*target.x-heading.x*target.z,heading.x*target.x+heading.z*target.z)
 var speed=xz(velocity).length()
 var desired_omega=2.0*maxf(speed,1.0)*sin(angle)/maxf(target.length(),0.5)
 steer=clampf(-desired_omega/(4.0*maxf(absf(car.linear_speed),0.2)),-1.0,1.0)
 Input.action_press("forward",throttle)
 Input.action_release("back")
 if steer<0:
  Input.action_press("left",-steer);Input.action_release("right")
 else:
  Input.action_press("right",steer);Input.action_release("left")
 return false

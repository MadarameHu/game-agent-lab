extends SceneTree
var checks=[]
var metrics={}
var main
var switcher
func _initialize():call_deferred('run')
func frames(n):
 for i in range(n):await physics_frame
func check(id,ok,summary):
 checks.append({'id':id,'pass':bool(ok),'summary':summary});print(id,' ',ok)
func tab():
 var e=InputEventKey.new();e.pressed=true;e.physical_keycode=KEY_TAB;e.keycode=KEY_TAB
 Input.parse_input_event(e)
 await process_frame
 e=InputEventKey.new();e.pressed=false;e.physical_keycode=KEY_TAB;e.keycode=KEY_TAB
 Input.parse_input_event(e)
 await process_frame
func vehicles():
 var count=0
 for child in main.get_children():
  if child is Vehicle:count+=1
 return count
func settle_fixture(car):
 car.set_physics_process(false)
 car.sphere.freeze=true
 car.sphere.linear_velocity=Vector3.ZERO;car.sphere.angular_velocity=Vector3.ZERO
 car.linear_speed=0;car.input=Vector3.ZERO
func run():
 main=load('res://scenes/main.tscn').instantiate();root.add_child(main)
 switcher=main.get_node('VehicleSwitcher')
 await frames(30)
 var bike=switcher.active
 check('default_motorcycle',switcher.motorcycle and bike.has_node('Container/Model/motorcycle') and bike.engine_sound.stream.resource_path.ends_with('engine-motorcycle.ogg') and main.get_node('View').target==bike,'Initial scene is actual motorcycle, dedicated engine audio and valid camera target')
 var start=bike.sphere.global_position
 Input.action_press('forward');await frames(90)
 var distance=bike.sphere.global_position.distance_to(start)
 var old_id=bike.get_instance_id();await tab()
 check('moving_tab_rejected',is_instance_valid(bike) and switcher.active.get_instance_id()==old_id and switcher.notice.text.contains('Stop first'),'Actual driving then Tab does not switch and shows stop-first message')
 metrics['motorcycle_distance_1_5s']=distance
 check('motorcycle_drives',distance>1.5,'Actual input moves motorcycle physics more than1.5m')
 Input.action_press('right');await frames(15)
 check('motorcycle_effects',abs(bike.motorcycle.rotation.z)>.02 and abs(bike.fork.rotation.y)>.02 and abs(bike.wheel_front.rotation.x)>.1,'Actual input triggers dedicated motorcycle lean, fork steering and wheel rotation')
 Input.action_release('forward');Input.action_release('right')
 # Stopping fixtures avoid relying on a test driver to park; vehicle swaps are real Tab events.
 settle_fixture(bike)
 var origin=bike.sphere.global_position
 var heading=bike.vehicle_model.global_basis
 var camera_position=main.get_node('View').global_position
 await tab()
 var truck=switcher.active
 check('stopped_tab_switch',not switcher.motorcycle and truck.has_node('Container/Model/body') and truck.sphere.global_position.distance_to(origin)<.03 and truck.vehicle_model.global_basis.z.dot(heading.z)>.999,'Stopped Tab replaces motorcycle by real yellow truck at same body position and heading')
 check('camera_and_single_vehicle',vehicles()==1 and not is_instance_valid(bike) and main.get_node('View').target==truck and main.get_node('View').global_position.distance_to(camera_position)<.4 and switcher.hud.text=='YELLOW TRUCK','Old vehicle freed, only1 controller, HUD updated and camera immediately rebound without jump')
 # Place truck back on known road after prior turning experiment.
 truck.sphere.freeze=true;truck.sphere.global_position=Vector3(3.5,.5,5);truck.vehicle_model.global_basis=Basis.IDENTITY;truck.sphere.linear_velocity=Vector3.ZERO;truck.sphere.angular_velocity=Vector3.ZERO
 truck.vehicle_model.global_position=Vector3(3.5,-.15,5);truck.raycast.global_position=Vector3(3.5,.5,5);truck.sphere.freeze=false
 await frames(15);start=truck.sphere.global_position
 Input.action_press('forward');await frames(90);Input.action_release('forward')
 metrics['truck_distance_1_5s']=truck.sphere.global_position.distance_to(start)
 check('truck_drives',metrics.truck_distance_1_5s>1.5,'New truck responds to actual forward input and moves its real rigidbody')
 var repeats=true
 for i in range(10):
  var previous=switcher.active;settle_fixture(previous)
  var p=previous.sphere.global_position;var b=previous.vehicle_model.global_basis
  await tab()
  repeats=repeats and vehicles()==1 and not is_instance_valid(previous) and main.get_node('View').target==switcher.active and switcher.active.sphere.global_position.distance_to(p)<.03 and switcher.active.vehicle_model.global_basis.z.dot(b.z)>.999
 check('ten_repeated_switches',repeats,'10 actual Tab cycles each preserve pose and leave exactly1 vehicle and valid camera')
 var f=FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE);f.store_string(JSON.stringify({'checks':checks,'metrics':metrics,'fixture':'Driving and Tab events are real Input. Stopped-switch checks inject zero speed; truck drive fixture resets to original road position.'},'  '))
 var ok=true
 for c in checks:ok=ok and c.pass
 quit(0 if ok else 2)

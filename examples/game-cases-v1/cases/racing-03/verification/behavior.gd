extends SceneTree
var checks=[]
var metrics={}
var car
var view
func _initialize():call_deferred('run')
func check(id,ok,summary):
 checks.append({'id':id,'pass':bool(ok),'summary':summary});print(id,' ',ok)
func frames(n):
 for i in range(n):await physics_frame
func run():
 var main=load('res://scenes/main.tscn').instantiate();root.add_child(main)
 car=main.get_node('Vehicle');view=main.get_node('View')
 await frames(30)
 var start=car.sphere.global_position
 Input.action_press('forward');await frames(120);Input.action_release('forward')
 metrics['actual_drive_distance']=car.sphere.global_position.distance_to(start)
 var forward_velocity=Vector3(car.sphere.linear_velocity.x,0,car.sphere.linear_velocity.z)
 var forward_lookahead=Vector3(view.lookahead.x,0,view.lookahead.z)
 metrics['real_input_lookahead']={'velocity':[forward_velocity.x,forward_velocity.y,forward_velocity.z],'lookahead':[forward_lookahead.x,forward_lookahead.y,forward_lookahead.z],'dot':forward_velocity.dot(forward_lookahead)}
 check('real_input_lookahead_direction',forward_velocity.dot(forward_lookahead)>1.0,'After actual forward Input, camera lookahead points ahead of real physical travel (velocity dot lookahead >1)')
 check('actual_input_drive',metrics.actual_drive_distance>2.0,'Actual forward Input and real rigidbody move more than 2m in two seconds')
 car.set_physics_process(false);car.sphere.freeze=true
 # The following are state-controlled product-function fixtures, not a claimed driven lap.
 car.linear_speed=1.0
 Input.action_press('back')
 car.handle_input(1.0/60);car._physics_process(1.0/60)
 var first=car.linear_speed
 for i in range(180):car._physics_process(1.0/60)
 check('brake_before_reverse',first>0 and first<1 and car.linear_speed<-.3,'S first brakes positive drive before settling into half-strength reverse')
 Input.action_release('back');car.linear_speed=1.0
 var monotonic=true;var prev=car.linear_speed
 for i in range(60):
  car._physics_process(1.0/60)
  monotonic=monotonic and car.linear_speed<=prev and car.linear_speed>=0;prev=car.linear_speed
 metrics['coast_after_1s']=car.linear_speed
 check('coast',monotonic and car.linear_speed>.05 and car.linear_speed<.3,'Coast decays continuously and monotonically instead of abrupt loss')
 Input.action_press('right');Input.action_press('forward')
 car.linear_speed=1;car.angular_speed=0;car.sphere.linear_velocity=Vector3(0,0,-1)
 for i in range(120):car._physics_process(1.0/60)
 var low=abs(car.angular_speed)
 car.angular_speed=0;car.sphere.linear_velocity=Vector3(0,0,-9)
 for i in range(120):car._physics_process(1.0/60)
 var high=abs(car.angular_speed)
 metrics['low_yaw_rate']=low;metrics['high_yaw_rate']=high
 check('speed_sensitive_steering',low>2.5 and high<1.2 and high>.5,'Physical speed gives useful low-speed turning and lower high-speed yaw')
 var max_step=0.0
 for i in range(240):
  if i%30==0:
   if Input.is_action_pressed('right'):Input.action_release('right');Input.action_press('left')
   else:Input.action_release('left');Input.action_press('right')
  var old=car.angular_speed;car._physics_process(1.0/60);max_step=max(max_step,abs(car.angular_speed-old))
 metrics['max_high_speed_yaw_step']=max_step
 check('continuous_turns',max_step<.2,'Alternating real input at injected high physical speed has bounded smooth yaw response (<0.2 rad/s each 60Hz tick)')
 Input.action_release('left');Input.action_release('right')
 var drive=car.drive_force;car.drive_force=50;car.sphere.angular_velocity=Vector3.ZERO;car.handle_input(1.0/60);var half=car.sphere.angular_velocity.length()
 car.drive_force=100;car.sphere.angular_velocity=Vector3.ZERO;car.handle_input(1.0/60);var full=car.sphere.angular_velocity.length();car.drive_force=drive
 var gain=car.low_speed_steering;car.low_speed_steering=2;var modified=car.steering_gain(1);car.low_speed_steering=gain
 check('parameter_effect',abs(full-half*2)<.01 and abs(modified-2)<.01,'Changing Inspector drive force changes applied angular drive; steering parameter changes product gain')
 Input.action_release('forward');view.set_physics_process(false);car.linear_speed=1;car.sphere.linear_velocity=Vector3.ZERO
 for i in range(300):view._physics_process(1.0/60)
 var near=view.camera.position.z
 car.sphere.linear_velocity=Vector3(0,0,-10)
 var z0=view.camera.position.z;view._physics_process(1.0/60);var first_zoom=abs(view.camera.position.z-z0)
 for i in range(300):view._physics_process(1.0/60)
 var far=view.camera.position.z;var ahead=view.lookahead.length()
 car.sphere.linear_velocity=Vector3.ZERO
 var descending=true;var oldz=view.camera.position.z
 for i in range(360):
  view._physics_process(1.0/60)
  descending=descending and view.camera.position.z<=oldz+.001;oldz=view.camera.position.z
 metrics['camera']={'near':near,'far':far,'first_step':first_zoom,'lookahead':ahead,'returned':view.camera.position.z}
 check('camera',near<10.1 and far>18 and ahead>3 and first_zoom<.1 and descending and view.camera.position.z<10.1,'Measured speed widens camera and advances focus; continuous easing returns to near view')
 var f=FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE);f.store_string(JSON.stringify({'checks':checks,'metrics':metrics,'fixture':'Only first test is uninterrupted real driving; other tests inject physical state then exercise product functions and real Input.'},'  '))
 var ok=true
 for c in checks:ok=ok and c.pass
 quit(0 if ok else 2)

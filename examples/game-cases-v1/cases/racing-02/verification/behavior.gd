extends SceneTree
var results=[]
var main
var manager
var sphere
func check(id,value,summary):
 results.append({'id':id,'pass':bool(value),'summary':summary})
 print(id,' ',value)
func frames(n):
 for i in range(n):await physics_frame
func _initialize():call_deferred('run')
func cross_gate(index,forward):
 var gate=manager.gates[index]
 sphere.freeze=true
 sphere.global_position=gate.global_position+Vector3(0,1.8,0)+gate.global_basis.z*(-2.2 if forward else 2.2)
 sphere.linear_velocity=Vector3.ZERO;sphere.angular_velocity=Vector3.ZERO
 await frames(4)
 sphere.freeze=false;sphere.linear_velocity=gate.global_basis.z*(3.0 if forward else -3.0)
 await frames(105)
 sphere.freeze=true
 await frames(4)
func run():
 main=load('res://scenes/main.tscn').instantiate();root.add_child(main)
 manager=main.get_node('RaceManager');sphere=main.get_node('Vehicle/Sphere')
 var initial=sphere.global_position
 Input.action_press('forward')
 await frames(100)
 check('countdown_input_lock',manager.state=='countdown' and not manager.car.controls_enabled and sphere.global_position.distance_to(initial)<0.02,'Actual forward Input during countdown leaves frozen body at spawn')
 await frames(110)
 check('countdown_go',manager.state=='running' and manager.car.controls_enabled and manager.elapsed>0,'Real 3 second timer releases controls and starts timing')
 Input.action_release('forward')
 # Trigger tests use the actual vehicle Sphere with injected start pose/velocity.
 # The physics engine carries it across real Area3D planes. This is NOT a driven lap.
 manager.car.set_physics_process(false);sphere.gravity_scale=0
 await cross_gate(0,true)
 await cross_gate(2,true)
 check('missing_and_out_of_order',manager.state=='running' and manager.next_gate==1,'Finish and CP2 before CP1 do not finish or advance')
 await cross_gate(1,false)
 check('reverse_checkpoint',manager.next_gate==1,'Reverse physical crossing of CP1 is rejected')
 await cross_gate(1,true)
 check('physical_cp1',manager.next_gate==2,'Physics body crossed CP1 forward and progressed')
 await cross_gate(3,true)
 check('skip_cp2',manager.next_gate==2,'CP3 before CP2 rejected')
 await cross_gate(2,true);await cross_gate(3,true)
 check('ordered_cp123',manager.next_gate==4,'Sequential physical crossings advance all three checkpoints')
 await cross_gate(0,false)
 check('reverse_finish',manager.state=='running','Reverse physical finish crossing does not finish')
 await cross_gate(0,true)
 check('correct_finish',manager.state=='finished' and manager.elapsed>0,'Forward physical finish after123 finishes and stores elapsed')
 var final_time=manager.elapsed;await frames(30)
 check('final_timer_stops',is_equal_approx(final_time,manager.elapsed),'Final displayed time is stable')
 var key=InputEventKey.new();key.pressed=true;key.physical_keycode=KEY_R;Input.parse_input_event(key)
 await frames(3)
 check('r_restart',manager.state=='countdown' and manager.next_gate==1 and manager.elapsed==0 and sphere.global_position.distance_to(initial)<0.02 and sphere.linear_velocity.length()<0.001 and sphere.angular_velocity.length()<0.001,'Real R event resets timer, checkpoint state, pose and physical velocities')
 var f=FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE);f.store_string(JSON.stringify({'checks':results,'fixture':'Body starting pose and velocity injected only in crossing tests; movement through Area3D is actual physics, not direct manager calls.'},'  '));f.close()
 var ok=results.all(func(r):return r['pass'])
 main.queue_free();await process_frame;quit(0 if ok else 2)

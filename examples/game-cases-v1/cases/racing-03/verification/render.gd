extends SceneTree
func _initialize():call_deferred('run')
func run():
 var main=load('res://scenes/main.tscn').instantiate();root.add_child(main)
 for i in range(100):await process_frame
 await RenderingServer.frame_post_draw
 var image=root.get_texture().get_image()
 var out=OS.get_cmdline_user_args()[0]
 var err=image.save_png(out+'/scene.png')
 Input.action_press('forward')
 for i in range(120):await physics_frame
 Input.action_release('forward')
 await RenderingServer.frame_post_draw
 var moving=root.get_texture().get_image()
 var moving_err=moving.save_png(out+'/scene-moving.png')
 var view=main.get_node('View');var car=main.get_node('Vehicle')
 var velocity=Vector3(car.sphere.linear_velocity.x,0,car.sphere.linear_velocity.z)
 var dot=velocity.dot(view.lookahead)
 var f=FileAccess.open(out+'/render.json',FileAccess.WRITE)
 f.store_string(JSON.stringify({'renderer':RenderingServer.get_current_rendering_method(),'width':image.get_width(),'height':image.get_height(),'save_error':err,'native':true,'moving_save_error':moving_err,'moving_image':'scene-moving.png','moving_input_physics_frames':120,'velocity':[velocity.x,velocity.y,velocity.z],'lookahead':[view.lookahead.x,view.lookahead.y,view.lookahead.z],'velocity_dot_lookahead':dot},'  '))
 quit(0 if err==OK and moving_err==OK and dot>1.0 else 2)

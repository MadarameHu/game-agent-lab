extends SceneTree
func _initialize():call_deferred('run')
func run():
 root.add_child(load('res://scenes/main.tscn').instantiate())
 for i in range(100):await process_frame
 await RenderingServer.frame_post_draw
 var image=root.get_texture().get_image()
 var out=OS.get_cmdline_user_args()[0]
 var err=image.save_png(out+'/scene.png')
 var f=FileAccess.open(out+'/render.json',FileAccess.WRITE)
 f.store_string(JSON.stringify({'renderer':RenderingServer.get_current_rendering_method(),'width':image.get_width(),'height':image.get_height(),'save_error':err,'native':true},'  '))
 quit(0 if err==OK else 2)

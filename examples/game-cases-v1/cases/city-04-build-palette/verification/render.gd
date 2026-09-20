extends SceneTree
func _initialize():
 call_deferred("run")
func run():
 var output = OS.get_cmdline_user_args()[0]
 var err = change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
 if err != OK: quit(2); return
 for i in range(100): await process_frame
 await RenderingServer.frame_post_draw
 var image = root.get_texture().get_image()
 var result = image.save_png(output.path_join("scene.png"))
 var b = current_scene.get_node("Builder")
 var report = {"screenshot_error":result,"renderer":RenderingServer.get_current_rendering_method(),"cells":b.gridmap.get_used_cells().size(),"cash":b.map.cash,"startup":"normal main scene, no fixture injection","frames":100,"width":image.get_width(),"height":image.get_height()}
 var f = FileAccess.open(output.path_join("render.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify(report,"  "))
 print("RENDER_COMPLETE "+JSON.stringify(report))
 quit(0 if result == OK else 3)

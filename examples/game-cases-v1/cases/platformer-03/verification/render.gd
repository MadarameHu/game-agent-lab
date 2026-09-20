extends SceneTree
var scene: Node3D
func _initialize(): call_deferred("capture")
func ticks(n):
	for i in range(n):
		await physics_frame
		await process_frame
func capture():
	var out: String = OS.get_cmdline_user_args()[0]
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await ticks(50)
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var err := img.save_png(out.path_join("scene.png"))
	var view=scene.get_node("View")
	var rotation_before=view.camera_rotation
	var zoom_before=view.zoom
	Input.action_press("camera_right")
	Input.action_press("zoom_in")
	await ticks(5)
	Input.action_release("camera_right")
	Input.action_release("zoom_in")
	var camera_works=view.camera_rotation.y>rotation_before.y and view.zoom<zoom_before
	var hud=scene.get_node("HUD")
	var hint=hud.get_node("ControlsHint")
	var coins=hud.get_node("Coins")
	var hint_rect=hint.get_global_rect()
	var coins_rect=coins.get_global_rect()
	var checks=[{"id":"camera_controls","pass":camera_works,"before_zoom":zoom_before,"after_zoom":view.zoom},{"id":"hint_placement","pass":not hint_rect.intersects(coins_rect) and Rect2(0,0,1280,720).encloses(hint_rect),"hint":str(hint_rect),"coins":str(coins_rect)}]
	var ok=err==OK and camera_works
	for c in checks: ok=ok and c.pass
	FileAccess.open(out.path_join("render.json"),FileAccess.WRITE).store_string(JSON.stringify({"native":DisplayServer.get_name()!="headless","renderer":RenderingServer.get_current_rendering_method(),"view":"Original gameplay camera and original layout","width":img.get_width(),"height":img.get_height(),"save_error":err,"checks":checks,"pass":ok,"human_review":null},"  "))
	quit(0 if ok else 1)

extends SceneTree
var scene: Node3D
var checks=[]
var out: String
func _initialize(): call_deferred("capture")
func ticks(n):
	for i in range(n):
		await physics_frame
		await process_frame
func check(id,ok,details):
	checks.append({"id":id,"pass":bool(ok),"details":details})
func snap(filename):
	await RenderingServer.frame_post_draw
	var img=root.get_texture().get_image()
	var err=img.save_png(out.path_join(filename))
	check("image_"+filename,err==OK and img.get_width()==1280 and img.get_height()==720,{"width":img.get_width(),"height":img.get_height(),"save_error":err})
func capture():
	out=OS.get_cmdline_user_args()[0]
	scene=load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene=scene
	await ticks(60)
	await snap("scene.png")
	var camera:=Camera3D.new()
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=19.5
	scene.add_child(camera)
	camera.position=Vector3(5,17,19)
	camera.look_at(Vector3(-6,1,-0.5))
	camera.current=true
	await ticks(10)
	await snap("overview.png")
	camera.position=Vector3(-27,11,7)
	camera.look_at(Vector3(-16,0,-0.5))
	camera.size=15
	await ticks(10)
	await snap("remote.png")
	var coins=[]
	var falling=[]
	for n in scene.get_node("World").get_children():
		if n.scene_file_path=="res://objects/coin.tscn": coins.append(n)
		if n.scene_file_path=="res://objects/platform_falling.tscn": falling.append(n)
	check("original_counts",coins.size()==14 and falling.size()==3,{"coins":coins.size(),"falling_platforms":falling.size()})
	var meshes=0
	for platform in falling:
		for mesh in platform.find_children("*","MeshInstance3D",true,false):
			if mesh.material_override and mesh.material_override.resource_path=="res://materials/dusk_hazard.tres": meshes+=1
	check("hazard_material",meshes>=3,{"hazard_meshes":meshes,"platform_count":falling.size()})
	var panel=scene.get_node("HUD/CoinPanel").get_global_rect()
	var icon=scene.get_node("HUD/Icon").get_global_rect()
	var count=scene.get_node("HUD/Coins")
	check("hud_padding",Rect2(0,0,1280,720).encloses(panel) and panel.position.x>=28 and panel.position.y>=28 and panel.encloses(icon),{"panel":str(panel),"icon":str(icon)})
	var env=scene.get_node("Environment").environment
	check("dusk_lighting",env.sky.sky_material is ProceduralSkyMaterial and env.sky.sky_material.sky_horizon_color.r>env.sky.sky_material.sky_horizon_color.b and env.sky.sky_material.sky_top_color.b>env.sky.sky_material.sky_top_color.r and not env.adjustment_enabled,{"horizon":str(env.sky.sky_material.sky_horizon_color),"zenith":str(env.sky.sky_material.sky_top_color),"background_energy":env.background_energy_multiplier,"sun_energy":scene.get_node("Sun").light_energy,"postprocess_tint":false})
	# Test fixture moves one original coin onto the live player for real body overlap.
	coins[0].global_position=scene.get_node("Player").global_position+Vector3(0,0.55,0)
	await ticks(6)
	check("coin_overlap",scene.get_node("Player").coins==1 and count.text=="1",{"coins":scene.get_node("Player").coins,"hud":count.text,"fixture":"one original coin moved to player after all screenshots"})
	var platform=falling[0]
	var initial_y=platform.position.y
	var player=scene.get_node("Player")
	player.global_position=platform.global_position+Vector3(0,1,0)
	player.velocity=Vector3.ZERO
	player.gravity=0
	await ticks(65)
	check("falling_mechanism",not is_instance_valid(platform) or platform.position.y<initial_y-0.2,{"fixture":"player placed above original falling platform; actual collision/physics","initial_y":initial_y,"current_y":platform.position.y if is_instance_valid(platform) else null})
	var ok=true
	for c in checks: ok=ok and c.pass
	FileAccess.open(out.path_join("render.json"),FileAccess.WRITE).store_string(JSON.stringify({"native":DisplayServer.get_name()!="headless","renderer":RenderingServer.get_current_rendering_method(),"view":"scene.png original spawn camera; overview/remote explicitly injected review cameras, layout untouched","width":1280,"height":720,"checks":checks,"pass":ok,"human_review":null},"  "))
	quit(0 if ok else 1)

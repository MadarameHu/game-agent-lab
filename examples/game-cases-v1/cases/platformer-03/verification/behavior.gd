extends SceneTree
var world: Node3D
var p
var checks = []
var out: String
func _initialize(): call_deferred("run_tests")
func tick(n=1):
	for i in range(n):
		await physics_frame
		await process_frame
func check(id, value, details):
	checks.append({"id":id,"pass":bool(value),"details":details})
func fixture(width=100.0):
	Input.action_release("jump")
	Input.action_release("move_right")
	if is_instance_valid(world):
		world.queue_free()
		await tick(2)
	world = Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	var collider := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(width, 0.5, 100)
	collider.shape = box
	floor_body.add_child(collider)
	floor_body.position.y = -0.25
	world.add_child(floor_body)
	var view := Node3D.new()
	world.add_child(view)
	p = load("res://objects/player.tscn").instantiate()
	p.view = view
	p.position.y = 0.1
	world.add_child(p)
	await tick(15)
	check("fixture_grounded",p.is_on_floor(),{"position":str(p.position),"fixture":"Original product player and original collider; test-only flat floor"})
func press():
	Input.action_press("jump")
	await tick()
	Input.action_release("jump")
func edge(delay_ticks):
	await fixture(4.0)
	Input.action_press("move_right")
	var n=0
	while p.is_on_floor() and n<100:
		await tick()
		n+=1
	Input.action_release("move_right")
	await tick(delay_ticks)
	var time_left=p.coyote_remaining
	await press()
	var first=p.gravity
	var air_available=p.jump_double
	await tick(3)
	await press()
	var second=p.gravity
	await tick(3)
	var before=p.gravity
	await press()
	check("coyote_inside" if delay_ticks<=6 else "coyote_outside",first<0 and air_available==(delay_ticks<=6) and (second < -6 if delay_ticks<=6 else second > first) and p.gravity>before,{"walk_off_ticks":n,"delay_ticks_after_walkoff":delay_ticks,"seconds_after_walkoff":float(delay_ticks+1)/60,"coyote_at_press":time_left,"first_gravity":first,"remaining_air_jump":air_available,"second_gravity":second,"third_gravity":p.gravity})
func buffer(target_time):
	await fixture()
	await press()
	await tick(5)
	await press()
	check("normal_double_jump",not p.jump_single and not p.jump_double and p.gravity < -6,{"gravity":p.gravity})
	var waited=0
	while waited<100:
		await tick()
		waited+=1
		var distance=maxf(0,p.position.y+0.05)
		var flight=(-p.gravity+sqrt(p.gravity*p.gravity+50*distance))/25.0
		if p.gravity>0 and flight<=target_time: break
	await press()
	var n=0
	var launched=false
	while n<40:
		await tick()
		n+=1
		if p.gravity<0:
			launched=true
			break
		if p.is_on_floor(): break
	check("buffer_inside" if target_time<0.15 else "buffer_outside", launched==(target_time<0.15),{"target_flight_seconds":target_time,"processed_press_to_landing_seconds":float(n)/60,"landing_jump":launched,"gravity":p.gravity,"input":"fresh Input press after exhausting both actual jumps"})
	if launched:
		await tick(3)
		await press()
		await tick(3)
		var before=p.gravity
		await press()
		check("buffer_no_third_jump",p.gravity>before and not p.jump_double,{"gravity_before":before,"after":p.gravity})
func run_tests():
	out=OS.get_cmdline_user_args()[0]
	await edge(4)
	await edge(9)
	await edge(6)
	await edge(7)
	await buffer(0.10)
	await buffer(0.23)
	await buffer(0.145)
	await buffer(0.205)
	await fixture()
	Input.action_press("jump")
	await tick(100)
	check("hold_no_autojump",p.is_on_floor() and p.gravity==0,{"held_seconds":100.0/60,"on_floor":p.is_on_floor(),"gravity":p.gravity})
	Input.action_release("jump")
	check("parameters",p.movement_speed==250 and p.jump_strength==7,{"speed":p.movement_speed,"jump":p.jump_strength})
	var ok=true
	for c in checks: ok=ok and c.pass
	FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"pass":ok,"checks":checks,"physics_ticks_per_second":Engine.physics_ticks_per_second,"note":"Input.action_press/release drives original product physics; fixture changes only test floor and spawn."},"  "))
	quit(0 if ok else 1)

extends SceneTree
var scene: Node3D
var player: CharacterBody3D
var results: Array = []
var out := ""
var collected := {}

func _initialize():
    out = OS.get_cmdline_user_args()[0]
    call_deferred("run_test")

func fresh_scene():
    if is_instance_valid(scene):
        root.remove_child(scene)
        scene.free()
    scene = load("res://scenes/main.tscn").instantiate()
    root.add_child(scene)
    current_scene = scene
    player = scene.get_node("Player")
    for i in range(20): await physics_frame

func controls(direction: Vector3):
    var local := direction.rotated(Vector3.UP,-scene.get_node("View").rotation.y)
    for action in ["move_left","move_right","move_forward","move_back"]: Input.action_release(action)
    if local.x < 0: Input.action_press("move_left",minf(-local.x,1))
    else: Input.action_press("move_right",minf(local.x,1))
    if local.z < 0: Input.action_press("move_forward",minf(-local.z,1))
    else: Input.action_press("move_back",minf(local.z,1))

func traverse(names: Array, fixture_start: bool) -> Dictionary:
    if fixture_start:
        var start: Node3D = scene.get_node("World/"+names[0])
        player.position = start.position+Vector3(0,0.48,0)
        player.velocity = Vector3.ZERO
        player.gravity = 0
        for i in range(10): await physics_frame
    var transitions := []
    for index in range(1,names.size()):
        var target_node: Node3D = scene.get_node_or_null("World/"+names[index])
        if target_node == null:
            return {"pass":false,"fixture_start":fixture_start,"transitions":transitions,"error":"Target platform vanished before arrival: "+names[index]}
        var target: Vector3 = target_node.position
        var landed := false
        var samples := []
        Input.action_press("jump")
        for step in range(240):
            if step == 1 or step == 17: Input.action_release("jump")
            if step == 16 and not player.is_on_floor(): Input.action_press("jump")
            var delta := Vector3(target.x-player.position.x,0,target.z-player.position.z)
            controls(delta.normalized()*minf(1.0,delta.length()*2))
            await physics_frame
            if step%10 == 0: samples.append([player.position.x,player.position.y,player.position.z])
            if step>12 and delta.length()<0.55 and player.is_on_floor() and player.position.y>=target.y+0.20:
                landed = true
                break
            if player.position.y < -3: break
        controls(Vector3.ZERO)
        Input.action_release("jump")
        transitions.append({"from":names[index-1],"to":names[index],"landed":landed,"samples":samples,"position":[player.position.x,player.position.y,player.position.z]})
        if not landed: break
    for node in scene.get_node("World").get_children():
        if node.scene_file_path == "res://objects/coin.tscn" and node.grabbed: collected[node.name]=true
    return {"pass":transitions.size()==names.size()-1 and transitions.all(func(t):return t.landed),"fixture_start":fixture_start,"transitions":transitions,"coins":player.coins}

func run_test():
    await fresh_scene()
    var coin_count := 0
    var fall_count := 0
    var brick_count := 0
    for node in scene.get_node("World").get_children():
        if node.scene_file_path == "res://objects/coin.tscn":coin_count+=1
        if node.scene_file_path == "res://objects/platform_falling.tscn":fall_count+=1
        if node.scene_file_path == "res://objects/brick.tscn":brick_count+=1
    results.append({"id":"required_inventory","pass":coin_count==14 and fall_count==3 and brick_count==3,"summary":"Live scene inventory","details":{"coins":coin_count,"falling":fall_count,"bricks":brick_count}})
    var main := await traverse(["platform","platform-medium","platform2","platform-grass-large-round","platform4","platform3","platform5","platform-medium3"],false)
    results.append({"id":"main_route_physics","pass":main["pass"],"summary":"Original Input and CharacterBody3D from untouched spawn through every main waypoint","details":main})
    FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"checks":results},"  "))
    await fresh_scene()
    var branch := await traverse(["platform2","platform-medium2","platform-falling","platform-falling2","platform-falling3","platform-grass-large-round2","platform6","platform-medium4","platform4"],true)
    results.append({"id":"branch_route_physics","pass":branch["pass"],"summary":"One fixture placement at branch junction, then continuous original Input through falling platforms and return","details":branch})
    results.append({"id":"all_coins_reachable","pass":collected.size()==14,"summary":"Union of actual body-triggered coin pickups across the two continuous traversals","details":{"collected_ids":collected.keys(),"count":collected.size()}})
    FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"checks":results},"  "))
    print("PLATFORMER_TEST "+JSON.stringify(results.map(func(r):return {"id":r.id,"pass":r["pass"]})))
    quit(0 if results.all(func(r):return r["pass"]) else 2)

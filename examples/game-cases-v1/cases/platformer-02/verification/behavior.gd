extends SceneTree
var main: Node3D
var player: CharacterBody3D
var checks: Array = []
var out: String
func _initialize():
    out = OS.get_cmdline_user_args()[0]
    call_deferred("test")
func wait_frames(n: int):
    for i in range(n): await physics_frame
func place_fixture(pos: Vector3):
    player.position = pos
    player.velocity = Vector3.ZERO
    player.gravity = 0
    await wait_frames(5)
func check(id: String, ok: bool, details: Dictionary):
    checks.append({"id":id,"pass":ok,"summary":id,"details":details})
    FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"checks":checks},"  "))
func test():
    root.size = Vector2i(1280,720)
    main = load("res://scenes/main.tscn").instantiate()
    root.add_child(main)
    current_scene = main
    player = main.get_node("Player")
    await wait_frames(20)
    await place_fixture(Vector3(0,3.48,-6))
    check("zero_coin_goal_rejected",not main.level_completed and main.at_goal and player.is_physics_processing(),{"coins":player.coins,"message":main.get_node("HUD").goal_label.text,"fixture":"Teleport onto real goal Area; real body-enter event"})
    await place_fixture(Vector3(0,.5,0))
    check("can_leave_locked_goal",not main.at_goal and player.is_physics_processing(),{})
    var coin_nodes := []
    for node in main.get_node("World").get_children():
        if node.scene_file_path=="res://objects/coin.tscn": coin_nodes.append(node)
    var picked := []
    for node in coin_nodes:
        if player.coins>=7: break
        if node.grabbed: continue
        await place_fixture(node.global_position-Vector3(0,.55,0))
        picked.append(node.name)
    var seven: int = player.coins
    var first = coin_nodes[0]
    await place_fixture(Vector3(0,.5,0))
    await place_fixture(first.global_position-Vector3(0,.55,0))
    check("coin_counts_once",player.coins==seven,{"before":seven,"after":player.coins,"fixture":"Repeated real body contact with already grabbed coin"})
    await place_fixture(Vector3(0,3.48,-6))
    check("seven_coin_goal_rejected",player.coins==7 and not main.level_completed and main.get_node("HUD").goal_label.text.contains("1 MORE"),{"coins":player.coins,"message":main.get_node("HUD").goal_label.text})
    await place_fixture(Vector3(0,.5,0))
    # Controlled world-state fixture to verify product restart resets consumed objects.
    main.get_node("World/brick").explode()
    main.get_node("World/platform-falling")._on_body_entered(player)
    await wait_frames(100)
    var consumed := not main.has_node("World/brick") and not main.has_node("World/platform-falling")
    for node in coin_nodes:
        if not node.grabbed:
            await place_fixture(node.global_position-Vector3(0,.55,0))
            break
    await place_fixture(Vector3(0,3.48,-6))
    check("eight_coin_goal_completes",player.coins>=8 and main.level_completed and not player.is_physics_processing() and is_instance_valid(main.get_node("HUD").restart_button),{"coins":player.coins,"completed":main.level_completed,"completion_count":main.completion_count,"consumed_fixture_objects":consumed})
    if DisplayServer.get_name()!="headless":
        await process_frame
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png(out.get_base_dir().path_join("success.png"))
    main._on_goal_entered(player)
    main._evaluate_goal()
    check("completion_is_idempotent",main.completion_count==1,{"count":main.completion_count})
    var old_id := main.get_instance_id()
    await process_frame
    await process_frame
    var panel_rect: Rect2 = main.get_node("HUD").success_panel.get_global_rect()
    var button_rect: Rect2 = main.get_node("HUD").restart_button.get_global_rect()
    var viewport_rect := Rect2(Vector2.ZERO,Vector2(root.size))
    var fully_visible := viewport_rect.encloses(panel_rect) and viewport_rect.encloses(button_rect)
    check("success_panel_visible",fully_visible,{"panel":str(panel_rect),"button":str(button_rect),"viewport":str(viewport_rect)})
    for pressed in [true,false]:
        var event := InputEventMouseButton.new()
        event.button_index = MOUSE_BUTTON_LEFT
        event.pressed = pressed
        event.position = button_rect.get_center()
        event.global_position = event.position
        root.push_input(event,true)
        await process_frame
    await wait_frames(15)
    var restarted := current_scene
    var restored: bool = restarted.get_instance_id()!=old_id and not restarted.level_completed and restarted.get_node("Player").coins==0 and restarted.get_node("Player").is_physics_processing()
    var coins := 0
    for node in restarted.get_node("World").get_children():
        if node.scene_file_path=="res://objects/coin.tscn" and not node.grabbed: coins+=1
    restored = restored and coins==14 and restarted.has_node("World/brick") and restarted.has_node("World/platform-falling")
    check("restart_restores_world",restored,{"coins":coins,"fixture":"Real Viewport mouse click at visible product button center; no manual world reset","old_scene_id":old_id,"new_scene_id":restarted.get_instance_id()})
    print("GOAL_TEST "+JSON.stringify(checks.map(func(c):return {"id":c.id,"pass":c["pass"]})))
    quit(0 if checks.all(func(c):return c["pass"]) else 2)

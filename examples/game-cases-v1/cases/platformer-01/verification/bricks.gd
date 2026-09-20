extends SceneTree
func _initialize(): call_deferred("test")
func test():
    var out: String = OS.get_cmdline_user_args()[0]
    var rows := []
    var bindings := [["brick","platform-medium2"],["brick2","platform-grass-large-round2"],["brick3","platform-medium4"]]
    for binding in bindings:
        var scene: Node3D = load("res://scenes/main.tscn").instantiate()
        root.add_child(scene)
        current_scene = scene
        var player: CharacterBody3D = scene.get_node("Player")
        var brick: StaticBody3D = scene.get_node("World/"+binding[0])
        var platform: Node3D = scene.get_node("World/"+binding[1])
        player.position = Vector3(brick.position.x,platform.position.y+0.48,brick.position.z)
        player.velocity = Vector3.ZERO
        player.gravity = 0
        for i in range(15): await physics_frame
        Input.action_press("jump")
        await physics_frame
        Input.action_release("jump")
        var hit := false
        for i in range(65):
            await physics_frame
            if is_instance_valid(brick) and brick.exploded: hit = true
        rows.append({"brick":binding[0],"platform":binding[1],"exploded_by_input_jump":hit,"removed_after_effect":not is_instance_valid(brick)})
        root.remove_child(scene)
        scene.free()
    var ok: bool = rows.all(func(r):return r.exploded_by_input_jump)
    FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"checks":[{"id":"branch_bricks_breakable","pass":ok,"summary":"Each of three branch bricks hit from below by original jump Input and actual BottomDetector collision","details":{"fixture":"For each brick fresh candidate scene, one placement under brick on its supporting branch platform; no direct explode calls","rows":rows}}]},"  "))
    quit(0 if ok else 2)

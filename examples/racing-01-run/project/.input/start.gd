extends SceneTree
## Observes an upstream initial scene. Does not implement any task request.
func _initialize() -> void:
    call_deferred("capture")

func capture() -> void:
    var output := ""
    var setup := "default"
    var args := OS.get_cmdline_user_args()
    for i in range(args.size()):
        if args[i] == "--preview-out" and i + 1 < args.size(): output = args[i+1]
        if args[i] == "--scene-setup" and i + 1 < args.size(): setup = args[i+1]
    var scene_path := str(ProjectSettings.get_setting("application/run/main_scene"))
    var err := change_scene_to_file(scene_path)
    if err != OK:
        push_error("Initial scene load failed: " + scene_path)
        quit(3)
        return
    await process_frame
    await process_frame
    if setup == "city-sample":
        # Load the bundled resource exactly as the upstream F3 handler does.
        # No simulated user input; no requested task changes are performed.
        var builder = current_scene.get_node("Builder")
        var initial_map = load("res://sample map/map.res").duplicate(true)
        builder.gridmap.clear()
        builder.map = initial_map
        for cell in initial_map.structures:
            builder.gridmap.set_cell_item(Vector3i(cell.position.x,0,cell.position.y),cell.structure,cell.orientation)
        builder.update_cash()
        print("INPUT_SETUP city-sample cells=" + str(builder.gridmap.get_used_cells().size()) + " cash=" + str(builder.map.cash))
    if output.is_empty(): return
    for i in range(120): await process_frame
    await RenderingServer.frame_post_draw
    DirAccess.make_dir_recursive_absolute(output)
    err = root.get_texture().get_image().save_png(output.path_join("scene.png"))
    var report := {"initial_setup":setup,"main_scene":scene_path,"engine_version":Engine.get_version_info().string,
        "rendering_method":RenderingServer.get_current_rendering_method(),
        "node_count":root.find_children("*", "", true, false).size(),
        "mesh_instances":root.find_children("*", "MeshInstance3D", true, false).size(),
        "collision_shapes":root.find_children("*", "CollisionShape3D", true, false).size(),
        "screenshot_error":err,"observation":"120 process frames; no requested task changes executed"}
    var file := FileAccess.open(output.path_join("preview.json"),FileAccess.WRITE)
    if file: file.store_string(JSON.stringify(report,"  ")+"\n")
    print("PREVIEW_COMPLETE " + JSON.stringify(report))
    quit(0 if err == OK else 4)

extends SceneTree
# Evidence-only observer. No gameplay edits or controller intervention.
func _initialize(): call_deferred("capture")
func capture():
    var out := ""
    var args := OS.get_cmdline_user_args()
    for i in range(args.size()):
        if args[i] == "--out" and i+1 < args.size(): out = args[i+1]
    if out.is_empty(): quit(2);return
    var err = change_scene_to_file(str(ProjectSettings.get_setting("application/run/main_scene")))
    if err != OK: quit(3);return
    for i in range(120): await process_frame
    await RenderingServer.frame_post_draw
    DirAccess.make_dir_recursive_absolute(out)
    root.get_texture().get_image().save_png(out.path_join("driver-view.png"))
    var grid: GridMap = current_scene.get_node("GridMap")
    var lo := Vector3(INF,0,INF)
    var hi := Vector3(-INF,0,-INF)
    for cell in grid.get_used_cells():
        if grid.get_cell_item(cell) not in [1,2,3,4,6]: continue
        var p := grid.to_global(grid.map_to_local(cell))
        lo.x=minf(lo.x,p.x);lo.z=minf(lo.z,p.z)
        hi.x=maxf(hi.x,p.x);hi.z=maxf(hi.z,p.z)
    var center := (lo+hi)*0.5
    var span := maxf(hi.x-lo.x,hi.z-lo.z)+12.0
    var camera := Camera3D.new()
    current_scene.add_child(camera)
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL
    camera.size=span*1.25
    camera.far=500
    camera.position=center+Vector3(0.65,1.35,0.9)*span
    camera.look_at(center,Vector3.UP)
    camera.current=true
    for i in range(3): await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out.path_join("overview.png"))
    var meta={"engine":Engine.get_version_info().string,"source":"actual main scene","overview_camera":"evidence-only orthographic camera, not product modification","bounds":{"min":str(lo),"max":str(hi)},"frames":123}
    var f=FileAccess.open(out.path_join("render.json"),FileAccess.WRITE)
    f.store_string(JSON.stringify(meta,"  "))
    print("RENDER_COMPLETE "+JSON.stringify(meta))
    quit()

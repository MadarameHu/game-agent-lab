extends SceneTree
var scene: Node3D
func _initialize(): call_deferred("capture")
func capture():
    var args := OS.get_cmdline_user_args()
    var out: String = args[0]
    scene = load("res://scenes/main.tscn").instantiate()
    root.add_child(scene)
    current_scene = scene
    for i in range(60): await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out.path_join("scene-default.png"))
    var mode := "original gameplay camera"
    if "--overview" in args:
        var camera := Camera3D.new()
        camera.projection = Camera3D.PROJECTION_ORTHOGONAL
        camera.size = 19.5
        scene.add_child(camera)
        camera.position = Vector3(5,17,19)
        camera.look_at(Vector3(-6,1,-0.5))
        camera.current = true
        mode = "external review overview camera; product camera unchanged"
    for i in range(10): await process_frame
    await RenderingServer.frame_post_draw
    var img := root.get_texture().get_image()
    var err := img.save_png(out.path_join("scene.png"))
    FileAccess.open(out.path_join("render.json"),FileAccess.WRITE).store_string(JSON.stringify({"native":DisplayServer.get_name()!="headless","renderer":RenderingServer.get_current_rendering_method(),"view":mode,"width":img.get_width(),"height":img.get_height(),"save_error":err,"human_review":null},"  "))
    quit(err)

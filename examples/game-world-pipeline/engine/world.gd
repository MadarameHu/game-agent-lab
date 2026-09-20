extends Node3D
## Independent public implementation. Rewards use geometry/physics only.

const GRID := 0.25
const CLEARANCE := 0.02
const OVERLAP_TOLERANCE := 0.004
const SPEED := 3.5
const MAX_STEPS := 2400
const WEIGHTS := {"scene_load":0.10, "bounds":0.15, "no_overlap":0.20, "route_exists":0.25, "rollout_reaches_goal":0.30}
const COLORS := {"crate":Color("bc8650"), "barrel":Color("529a9b"), "shelf":Color("75889f")}

var spec: Dictionary = {}
var out_dir := ""
var play_mode := false
var load_errors: Array[String] = []
var checks: Array[Dictionary] = []
var obstacle_bodies: Array[StaticBody3D] = []
var actor: CharacterBody3D
var start_pos := Vector3(-4,0,0)
var goal_pos := Vector3(4,0,0)
var actor_radius := 0.3
var actor_height := 1.6
var goal_radius := 0.65
var room_width := 12.0
var room_depth := 10.0
var route: Array[Vector3] = []
var rollout_path: Array = []
var route_index := 0
var rollout_steps := 0
var run_active := false
var reached_goal := false
var finished := false
var warmup_frames := 0
var status_label: Label
var detail_label: Label
var badge_label: Label
var occupancy_count := 0
var blocked_count := 0
var min_move := INF
var previous_position := Vector3.ZERO
var stagnant_steps := 0
var visual_assets: Array[Dictionary] = []
var play_tap_direction := Vector3.ZERO
var play_tap_remaining := 0.0

func _ready() -> void:
    var args := OS.get_cmdline_user_args()
    var spec_path := ""
    for i in range(args.size()):
        if args[i] == "--spec" and i + 1 < args.size(): spec_path = args[i+1]
        if args[i] == "--out" and i + 1 < args.size(): out_dir = args[i+1]
        if args[i] == "--play": play_mode = true
    if out_dir.is_empty(): out_dir = OS.get_user_data_dir().path_join("last_run")
    DirAccess.make_dir_recursive_absolute(out_dir)
    if not FileAccess.file_exists(spec_path):
        load_errors.append("Cannot read scene JSON: " + spec_path)
    else:
        var parser := JSON.new()
        var err := parser.parse(FileAccess.get_file_as_string(spec_path))
        if err != OK or not parser.data is Dictionary:
            load_errors.append("Scene JSON must be a valid object: " + parser.get_error_message())
        else:
            spec = parser.data
            validate_spec()
    build_environment()
    build_hud()
    if not load_errors.is_empty():
        add_check("scene_load", false, {"errors":load_errors})
        for key in ["bounds","no_overlap","route_exists","rollout_reaches_goal"]:
            add_check(key, false, {"skipped":"Scene schema validation failed"})
        call_deferred("finish_run")
        return
    room_width = float(spec.room.width)
    room_depth = float(spec.room.depth)
    start_pos = vec(spec.player.position)
    goal_pos = vec(spec.goal.position)
    actor_radius = float(spec.player.radius)
    actor_height = float(spec.player.height)
    goal_radius = float(spec.goal.radius)
    build_room()
    build_actor()
    add_check("scene_load", true, {"object_count":spec.objects.size(), "schema_version":1, "positions":"object/player y is ground-based", "visual_assets":visual_assets,"collision_authority":"Axis-aligned BoxShape3D fitted to declared size"})
    status_label.text = "PLAYTEST" if play_mode else "VERIFYING THE WORLD"
    detail_label.text = "WASD / Arrow keys · R reset · Esc close" if play_mode else "Physics clearance → grid BFS → CharacterBody3D rollout"

func validate_spec() -> void:
    if int(spec.get("schema_version",0)) != 1: load_errors.append("schema_version must be 1")
    for key in ["room","player","goal"]:
        if not spec.get(key) is Dictionary: load_errors.append(key+" must be an object")
    if not spec.get("objects") is Array: load_errors.append("objects must be an array")
    if not load_errors.is_empty(): return
    for key in ["width","depth","height"]:
        if not positive_number(spec.room.get(key)): load_errors.append("room."+key+" must be positive")
    for key in ["player","goal"]:
        if not is_vec(spec[key].get("position")): load_errors.append(key+".position must contain 3 finite numbers")
        if not positive_number(spec[key].get("radius")): load_errors.append(key+".radius must be positive")
    if not positive_number(spec.player.get("height")): load_errors.append("player.height must be positive")
    if spec.objects.size() < 6: load_errors.append("At least six objects required")
    if spec.objects.size() > 80: load_errors.append("Maximum 80 objects in this small-room verifier")
    var ids := {}
    for obj in spec.objects:
        if not obj is Dictionary:
            load_errors.append("Each object must be a dictionary")
            continue
        var id := str(obj.get("id",""))
        if id.is_empty() or ids.has(id): load_errors.append("Object IDs must be nonempty and unique: "+id)
        ids[id] = true
        if not COLORS.has(str(obj.get("asset",""))): load_errors.append("Unsupported asset: "+id)
        if not is_vec(obj.get("position")): load_errors.append("Invalid position: "+id)
        if not is_vec(obj.get("size")):
            load_errors.append("Invalid size: "+id)
        else:
            for value in obj.size:
                if float(value) < 0.1 or float(value) > 12: load_errors.append("Object dimensions must be in [0.1,12]: "+id)
        if float(obj.get("rotation_y",0)) != 0: load_errors.append("v1 supports rotation_y=0 only: "+id)
    if not load_errors.is_empty(): return
    if not is_equal_approx(float(spec.room.width),12.0) or not is_equal_approx(float(spec.room.depth),10.0) or not is_equal_approx(float(spec.room.height),3.0):
        load_errors.append("v1 fixed room dimensions must stay [12,10,3]")
    if vec(spec.player.position).distance_to(Vector3(-4,0,0)) > 0.001 or not is_equal_approx(float(spec.player.radius),0.3) or not is_equal_approx(float(spec.player.height),1.6):
        load_errors.append("v1 player must stay at [-4,0,0], radius .30, height 1.6")
    if vec(spec.goal.position).distance_to(Vector3(4,0,0)) > 0.001 or not is_equal_approx(float(spec.goal.radius),0.65):
        load_errors.append("v1 goal must stay at [4,0,0], radius .65")

func positive_number(value: Variant) -> bool:
    return (value is float or value is int) and is_finite(float(value)) and float(value) > 0

func is_vec(value: Variant) -> bool:
    if not value is Array or value.size() != 3: return false
    for item in value:
        if not (item is float or item is int) or not is_finite(float(item)): return false
    return true

func vec(value: Array) -> Vector3:
    return Vector3(float(value[0]),float(value[1]),float(value[2]))

func packed_vec(value: Vector3) -> Array:
    return [snappedf(value.x,0.0001),snappedf(value.y,0.0001),snappedf(value.z,0.0001)]

func material(color: Color, metallic: float = 0.0) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.roughness = 0.74
    mat.metallic = metallic
    return mat

func box_mesh(parent: Node3D, center: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
    var mesh := MeshInstance3D.new()
    var shape := BoxMesh.new()
    shape.size = size
    mesh.mesh = shape
    mesh.material_override = material(color)
    parent.add_child(mesh)
    mesh.position = center
    return mesh

func static_box(node_name: String, center: Vector3, size: Vector3, layer: int) -> StaticBody3D:
    var body := StaticBody3D.new()
    body.name = node_name
    body.collision_layer = layer
    body.collision_mask = 0
    add_child(body)
    body.position = center
    var collider := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    shape.size = size
    collider.shape = shape
    body.add_child(collider)
    return body

func build_environment() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color("14202e")
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color("b5cde5")
    env.ambient_light_energy = 0.36
    env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    world.environment = env
    add_child(world)
    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-56,-32,0)
    light.light_color = Color("fff0d6")
    light.light_energy = 0.78
    light.shadow_enabled = true
    add_child(light)
    var camera := Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = 17.4
    camera.position = Vector3(11,17,15)
    add_child(camera)
    camera.look_at(Vector3(0,0.1,0),Vector3.UP)
    camera.current = true

func build_room() -> void:
    var floor_body := static_box("Ground",Vector3(0,-0.16,0),Vector3(room_width+0.5,0.32,room_depth+0.5),2)
    box_mesh(floor_body,Vector3.ZERO,Vector3(room_width+0.5,0.32,room_depth+0.5),Color("586674"))
    for x in range(-5,6): box_mesh(self,Vector3(x,0.006,0),Vector3(0.013,0.01,room_depth),Color("71808b"))
    for z in range(-4,5): box_mesh(self,Vector3(0,0.006,z),Vector3(room_width,0.01,0.013),Color("71808b"))
    var wall_data := [[Vector3(-room_width/2-0.10,1.5,0),Vector3(0.2,3,room_depth+0.4)], [Vector3(room_width/2+0.10,1.5,0),Vector3(0.2,3,room_depth+0.4)], [Vector3(0,1.5,-room_depth/2-0.10),Vector3(room_width,3,0.2)], [Vector3(0,1.5,room_depth/2+0.10),Vector3(room_width,3,0.2)]]
    for i in range(wall_data.size()):
        var data: Array = wall_data[i]
        var wall := static_box("Boundary_"+str(i),data[0],data[1],1)
        var visual_size: Vector3 = data[1]
        visual_size.y = 0.45
        box_mesh(wall,Vector3(0,-1.275,0),visual_size,Color("b5c5ce"))
        box_mesh(wall,Vector3(0,-1.02,0),Vector3(visual_size.x,0.06,visual_size.z),Color("e9b75f"))
    for obj in spec.objects:
        var size := vec(obj.size)
        var bottom := vec(obj.position)
        var body := static_box(str(obj.id),bottom+Vector3(0,size.y/2,0),size,1)
        body.set_meta("object_id",str(obj.id))
        obstacle_bodies.append(body)
        var asset_loaded := add_asset_visual(body,str(obj.asset),size)
        visual_assets.append({"object_id":str(obj.id),"asset":str(obj.asset),"mode":"glb" if asset_loaded else "procedural_fallback","path":"res://assets/"+str(obj.asset)+".glb" if asset_loaded else "built-in box mesh","license":"CC0 1.0 / Kenney Survival Kit (see project assets manifest)" if asset_loaded else "project MIT implementation"})
        if not asset_loaded:
            box_mesh(body,Vector3.ZERO,size,COLORS[str(obj.asset)])
            for side in [-1,1]:
                box_mesh(body,Vector3(side*size.x*0.36,0,-size.z/2-0.008),Vector3(size.x*0.06,size.y*0.94,0.022),Color("e1b978"))
                box_mesh(body,Vector3(0,side*size.y*0.36,-size.z/2-0.018),Vector3(size.x*0.94,size.y*0.055,0.025),Color("664a38"))
        var label := Label3D.new()
        label.text = str(obj.id).to_upper()
        label.position = Vector3(0,size.y/2+0.22,0)
        label.font_size = 32
        label.pixel_size = 0.008
        label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
        label.modulate = Color("fff6dd")
        label.outline_size = 8
        body.add_child(label)
    ground_marker(start_pos,0.53,Color("62bc8a"),"START")
    ground_marker(goal_pos,goal_radius,Color("eab052"),"EXIT")

func add_asset_visual(body: Node3D, asset: String, size: Vector3) -> bool:
    var asset_path := "res://assets/"+asset+".glb"
    if not ResourceLoader.exists(asset_path): return false
    var resource = load(asset_path)
    if not resource is PackedScene: return false
    var visual = resource.instantiate()
    if not visual is Node3D:
        visual.queue_free()
        return false
    body.add_child(visual)
    var meshes: Array[Node] = visual.find_children("*","MeshInstance3D",true,false)
    var bounds := AABB()
    var has_bounds := false
    for mesh in meshes:
        var relative: Transform3D = visual.global_transform.affine_inverse()*mesh.global_transform
        var local_bounds: AABB = relative*mesh.get_aabb()
        bounds = bounds.merge(local_bounds) if has_bounds else local_bounds
        has_bounds = true
    if not has_bounds or bounds.size.x < 0.001 or bounds.size.y < 0.001 or bounds.size.z < 0.001:
        visual.queue_free()
        return false
    visual.scale = size/bounds.size
    visual.position = -bounds.get_center()*visual.scale
    return true

func ground_marker(pos: Vector3, radius: float, color: Color, title: String) -> void:
    var cylinder := CylinderMesh.new()
    cylinder.top_radius = radius
    cylinder.bottom_radius = radius
    cylinder.height = 0.025
    var mesh := MeshInstance3D.new()
    mesh.mesh = cylinder
    mesh.material_override = material(color)
    mesh.position = pos+Vector3(0,0.022,0)
    add_child(mesh)
    var label := Label3D.new()
    label.text = title
    label.font_size = 50
    label.pixel_size = 0.006
    label.position = pos+Vector3(0,0.20,0.82)
    label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    label.modulate = color
    label.outline_size = 9
    add_child(label)

func build_actor() -> void:
    actor = CharacterBody3D.new()
    actor.name = "Player"
    actor.collision_layer = 4
    actor.collision_mask = 3
    actor.safe_margin = 0.001
    add_child(actor)
    actor.position = start_pos
    var collision := CollisionShape3D.new()
    var shape := CapsuleShape3D.new()
    shape.radius = actor_radius
    shape.height = actor_height
    collision.shape = shape
    collision.position.y = actor_height/2
    actor.add_child(collision)
    var mesh := MeshInstance3D.new()
    var capsule := CapsuleMesh.new()
    capsule.radius = actor_radius
    capsule.height = actor_height
    mesh.mesh = capsule
    mesh.material_override = material(Color("ecf4fa"))
    mesh.position.y = actor_height/2
    actor.add_child(mesh)
    var visor := box_mesh(actor,Vector3(0,1.14,0.24),Vector3(0.37,0.22,0.10),Color("213b50"))
    visor.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func build_hud() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var panel := ColorRect.new()
    panel.color = Color(0.025,0.05,0.075,0.94)
    panel.position = Vector2(28,24)
    panel.size = Vector2(1384,116)
    layer.add_child(panel)
    status_label = Label.new()
    status_label.position = Vector2(52,37)
    status_label.add_theme_font_size_override("font_size",30)
    status_label.add_theme_color_override("font_color",Color("f2f0e9"))
    status_label.text = "WAREHOUSE / WORLD DEVELOPMENT"
    layer.add_child(status_label)
    detail_label = Label.new()
    detail_label.position = Vector2(54,85)
    detail_label.add_theme_font_size_override("font_size",19)
    detail_label.add_theme_color_override("font_color",Color("a7bbca"))
    layer.add_child(detail_label)
    badge_label = Label.new()
    badge_label.position = Vector2(38,925)
    badge_label.add_theme_font_size_override("font_size",20)
    badge_label.add_theme_color_override("font_color",Color("d0dde5"))
    badge_label.text = "INDEPENDENT DEMO  /  GODOT PHYSICS  /  0.25 m GRID  /  CAPSULE RADIUS 0.30 m"
    layer.add_child(badge_label)

func _physics_process(delta: float) -> void:
    if actor == null or finished: return
    warmup_frames += 1
    if warmup_frames < 4: return
    if warmup_frames == 4:
        validate_geometry()
        route = find_route()
        add_check("route_exists",not route.is_empty(),{"algorithm":"4-neighbor grid BFS with actual PhysicsDirectSpaceState3D capsule occupancy", "grid_m":GRID,"capsule_radius_m":actor_radius,"clearance_margin_m":CLEARANCE,"probed_cells":occupancy_count,"blocked_cells":blocked_count,"path_nodes":route.size()})
        if play_mode:
            badge_label.text = "WASD / ARROWS TO MOVE  ·  R TO RESET  ·  ESC TO CLOSE  /  FIND THE GOLD EXIT"
            return
        if route.is_empty():
            add_check("rollout_reaches_goal",false,{"reason":"No collision-free BFS route; rollout not attempted"})
            finish_run()
            return
        route_index = 1
        rollout_path.append(packed_vec(actor.position))
        previous_position = actor.position
        run_active = true
    if play_mode:
        var direction := Vector3.ZERO
        if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP): direction.z -= 1
        if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN): direction.z += 1
        if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT): direction.x -= 1
        if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT): direction.x += 1
        if direction.is_zero_approx() and play_tap_remaining > 0.0:
            direction = play_tap_direction
        play_tap_remaining = maxf(0.0,play_tap_remaining-delta)
        move_actor(direction.normalized()*SPEED,delta)
        if horizontal_distance(actor.position,goal_pos) <= goal_radius:
            status_label.text = "EXIT REACHED  /  WELL DONE"
            status_label.add_theme_color_override("font_color",Color("a1e6ac"))
        return
    if not run_active: return
    rollout_steps += 1
    if horizontal_distance(actor.position,goal_pos) <= goal_radius:
        reached_goal = true
        rollout_path.append(packed_vec(actor.position))
        add_check("rollout_reaches_goal",true,{"distance_to_goal":horizontal_distance(actor.position,goal_pos),"goal_radius":goal_radius,"physics_steps":rollout_steps,"collision_motion":"CharacterBody3D.move_and_slide, gravity, fixed 60Hz"})
        finish_run()
        return
    while route_index < route.size()-1 and horizontal_distance(actor.position,route[route_index]) < 0.10:
        route_index += 1
    var target := route[mini(route_index,route.size()-1)]
    var direction := Vector3(target.x-actor.position.x,0,target.z-actor.position.z)
    var velocity := direction.normalized()*minf(SPEED,direction.length()/maxf(delta,0.001))
    move_actor(velocity,delta)
    if rollout_steps % 6 == 0: rollout_path.append(packed_vec(actor.position))
    if horizontal_distance(actor.position,previous_position) < 0.0005: stagnant_steps += 1
    else: stagnant_steps = 0
    previous_position = actor.position
    if rollout_steps >= MAX_STEPS or stagnant_steps > 120 or actor.position.y < -0.2:
        add_check("rollout_reaches_goal",false,{"reason":"Timeout, grounded actor stuck, or fell below floor", "physics_steps":rollout_steps,"stagnant_steps":stagnant_steps,"distance_to_goal":horizontal_distance(actor.position,goal_pos)})
        finish_run()

func move_actor(horizontal_velocity: Vector3, delta: float) -> void:
    actor.velocity.x = horizontal_velocity.x
    actor.velocity.z = horizontal_velocity.z
    actor.velocity.y -= 12.0*delta
    if actor.is_on_floor(): actor.velocity.y = -0.1
    actor.move_and_slide()

func horizontal_distance(a: Vector3,b: Vector3) -> float:
    return Vector2(a.x,a.z).distance_to(Vector2(b.x,b.z))

func validate_geometry() -> void:
    var invalid: Array[String] = []
    var overlaps: Array = []
    for i in range(spec.objects.size()):
        var obj: Dictionary = spec.objects[i]
        var bottom := vec(obj.position)
        var size := vec(obj.size)
        if absf(bottom.x)+size.x/2 > room_width/2+0.001 or absf(bottom.z)+size.z/2 > room_depth/2+0.001 or bottom.y < -0.001 or bottom.y+size.y > float(spec.room.height)+0.001:
            invalid.append(str(obj.id))
        var query := PhysicsShapeQueryParameters3D.new()
        var shape := BoxShape3D.new()
        shape.size = size-Vector3.ONE*OVERLAP_TOLERANCE
        query.shape = shape
        query.transform = obstacle_bodies[i].global_transform
        query.collision_mask = 1
        query.exclude = [obstacle_bodies[i].get_rid()]
        query.margin = 0.0
        var hits := get_world_3d().direct_space_state.intersect_shape(query,100)
        for hit in hits:
            if hit.collider.has_meta("object_id"):
                var other := str(hit.collider.get_meta("object_id"))
                if str(obj.id) < other: overlaps.append([str(obj.id),other])
    add_check("bounds",invalid.is_empty(),{"outside_object_ids":invalid,"tolerance_m":0.001,"room_inner_bounds":[-room_width/2,room_width/2,-room_depth/2,room_depth/2],"height_limit":float(spec.room.height)})
    add_check("no_overlap",overlaps.is_empty(),{"overlapping_pairs":overlaps,"query":"PhysicsDirectSpaceState3D.intersect_shape over BoxShape3D colliders", "probe_total_shrink_m":OVERLAP_TOLERANCE})

func is_clear(point: Vector3) -> bool:
    if absf(point.x)+actor_radius+CLEARANCE >= room_width/2 or absf(point.z)+actor_radius+CLEARANCE >= room_depth/2: return false
    var query := PhysicsShapeQueryParameters3D.new()
    var capsule := CapsuleShape3D.new()
    capsule.radius = actor_radius+CLEARANCE
    capsule.height = actor_height+2*CLEARANCE
    query.shape = capsule
    query.transform = Transform3D(Basis.IDENTITY,point+Vector3(0,actor_height/2+CLEARANCE,0))
    query.collision_mask = 1
    query.margin = 0.0
    return get_world_3d().direct_space_state.intersect_shape(query,1).is_empty()

func find_route() -> Array[Vector3]:
    var width := int(room_width/GRID)+1
    var depth := int(room_depth/GRID)+1
    var clear := PackedByteArray()
    clear.resize(width*depth)
    for zi in range(depth):
        for xi in range(width):
            var p := Vector3(-room_width/2+xi*GRID,0,-room_depth/2+zi*GRID)
            occupancy_count += 1
            if is_clear(p): clear[zi*width+xi] = 1
            else: blocked_count += 1
    var start_x := int(round((start_pos.x+room_width/2)/GRID))
    var start_z := int(round((start_pos.z+room_depth/2)/GRID))
    var goal_x := int(round((goal_pos.x+room_width/2)/GRID))
    var goal_z := int(round((goal_pos.z+room_depth/2)/GRID))
    var first := start_z*width+start_x
    var last := goal_z*width+goal_x
    var result: Array[Vector3] = []
    if not is_clear(start_pos) or not is_clear(goal_pos) or clear[first] == 0 or clear[last] == 0: return result
    var parent := PackedInt32Array()
    parent.resize(width*depth)
    parent.fill(-1)
    parent[first] = first
    var queue: Array[int] = [first]
    var head := 0
    var neighbors := [Vector2i(1,0),Vector2i(0,1),Vector2i(0,-1),Vector2i(-1,0)]
    while head < queue.size() and parent[last] == -1:
        var current := queue[head]
        head += 1
        var x := current%width
        var z := int(current/width)
        for offset in neighbors:
            var nx: int = x+offset.x
            var nz: int = z+offset.y
            if nx < 0 or nx >= width or nz < 0 or nz >= depth: continue
            var nxt := nz*width+nx
            if clear[nxt] == 1 and parent[nxt] == -1:
                parent[nxt] = current
                queue.append(nxt)
    if parent[last] == -1: return result
    var cursor := last
    while true:
        result.push_front(Vector3(-room_width/2+(cursor%width)*GRID,0,-room_depth/2+int(cursor/width)*GRID))
        if cursor == first: break
        cursor = parent[cursor]
    result[0] = start_pos
    result[result.size()-1] = goal_pos
    return result

func add_check(id: String, passed: bool, details: Dictionary) -> void:
    checks.append({"id":id,"pass":passed,"weight":WEIGHTS[id],"details":details})

func finish_run() -> void:
    if finished: return
    finished = true
    run_active = false
    var hard_pass := true
    var reward := 0.0
    var hints: Array[String] = []
    for check in checks:
        hard_pass = hard_pass and bool(check["pass"])
        if check["pass"]: reward += float(check.weight)
        else:
            match str(check.id):
                "scene_load": hints.append("Fix schema validation errors, preserve at least six stable object IDs and fixed room/player/goal.")
                "bounds": hints.append("Move listed objects fully inside room x=[-6,6], z=[-5,5], y=[0,3], accounting for half-width/depth and full height.")
                "no_overlap": hints.append("Separate listed pairs of colliders; preserve a margin between their axis-aligned boxes.")
                "route_exists": hints.append("Create a continuous ground corridor from [-4,0,0] to [4,0,0]; keep at least 0.80 m gap for radius-0.30 capsule plus grid/clearance margin. Move boxes blocking the middle barrier, preserve all object IDs.")
                "rollout_reaches_goal": hints.append("Ensure the corridor is wide enough for the real CharacterBody3D capsule and does not block spawn or goal.")
    var payload := {"schema_version":1,"engine":{"name":"Godot","version":Engine.get_version_info().string,"renderer":"gl_compatibility","headless":DisplayServer.get_name()=="headless"},"checks":checks,"hard_pass":hard_pass,"engine_reward":snappedf(reward,0.0001),"repair_hints":hints,"rollout":{"reached_goal":reached_goal,"steps":rollout_steps,"path":rollout_path,"goal_radius":goal_radius,"physics_hz":60,"max_steps":MAX_STEPS,"planner":"4-neighbor BFS on physics-probed 0.25m grid; not NavMesh","limitations":"Axis-aligned static boxes; ground-plane walking only; finite grid can conservatively miss narrow routes; overlap probes shrink boxes 4mm total; no aesthetics or human proxy score"}}
    var file := FileAccess.open(out_dir.path_join("checks.json"),FileAccess.WRITE)
    if file: file.store_string(JSON.stringify(payload,"  ")+"\n")
    status_label.text = "PASS  /  EXIT REACHED" if hard_pass else "BLOCKED  /  REPAIR REQUIRED"
    status_label.add_theme_color_override("font_color",Color("b6e5b4") if hard_pass else Color("ffc07a"))
    detail_label.text = "Engine reward %.2f  ·  %d physics steps  ·  %d objects" % [reward,rollout_steps,spec.get("objects",[]).size()]
    for i in range(0,rollout_path.size(),2):
        var p := vec(rollout_path[i])
        box_mesh(self,Vector3(p.x,0.032,p.z),Vector3(0.075,0.025,0.075),Color("d4ed9c"))
    if DisplayServer.get_name() != "headless":
        await get_tree().process_frame
        await RenderingServer.frame_post_draw
        var image := get_viewport().get_texture().get_image()
        var err := image.save_png(out_dir.path_join("scene.png"))
        if err != OK: push_error("Screenshot save failed: "+str(err))
    print("ENGINE_CHECKS "+JSON.stringify({"hard_pass":hard_pass,"engine_reward":reward,"steps":rollout_steps,"out":out_dir}))
    get_tree().quit(0)

func _unhandled_key_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_ESCAPE: get_tree().quit()
        if play_mode:
            var tap := Vector3.ZERO
            var code: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
            match code:
                KEY_W, KEY_UP: tap.z = -1
                KEY_S, KEY_DOWN: tap.z = 1
                KEY_A, KEY_LEFT: tap.x = -1
                KEY_D, KEY_RIGHT: tap.x = 1
            if not tap.is_zero_approx():
                play_tap_direction = tap
                play_tap_remaining = 0.12
        if event.keycode == KEY_R and play_mode and actor != null:
            actor.position = start_pos
            actor.velocity = Vector3.ZERO
            play_tap_direction = Vector3.ZERO
            play_tap_remaining = 0.0
            status_label.text = "PLAYTEST"
            status_label.add_theme_color_override("font_color",Color("f2f0e9"))

extends Area3D
signal crossed(number: int, forward: bool)
var number := 0
var target: RigidBody3D
var previous := {}
func setup(index: int, body: RigidBody3D, heading: Vector3):
 number = index
 target = body
 rotation.y = atan2(heading.x, heading.z)
 collision_layer = 0
 collision_mask = body.collision_layer
 monitoring = true
 var shape = CollisionShape3D.new()
 var box = BoxShape3D.new()
 box.size = Vector3(6.4, 4, 2.4)
 shape.shape = box
 shape.position.y = 1.3
 add_child(shape)
 for x in [-3.15, 3.15]:
  var post = MeshInstance3D.new()
  var mesh = BoxMesh.new()
  mesh.size = Vector3(0.12, 2.7, 0.12)
  post.mesh = mesh
  post.position = Vector3(x, 1.15, 0)
  var material = StandardMaterial3D.new()
  material.albedo_color = Color(0.18,0.9,0.75) if number else Color(1,0.75,0.25)
  material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
  post.material_override = material
  add_child(post)
 var label = Label3D.new()
 label.text = 'CP %d' % number if number else 'START / FINISH'
 label.position = Vector3(0, 3.0, 0)
 label.font_size = 64
 label.pixel_size = 0.006
 label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
 label.no_depth_test = true
 add_child(label)
 body_entered.connect(_entered)
 body_exited.connect(_exited)
func _entered(body):
 if body == target: previous[body.get_instance_id()] = to_local(body.global_position).z
func _exited(body): previous.erase(body.get_instance_id())
func reset_tracking(): previous.clear()
func _physics_process(_delta):
 if not is_instance_valid(target): return
 var key = target.get_instance_id()
 if not previous.has(key): return
 var z = to_local(target.global_position).z
 var before = float(previous[key])
 var velocity = target.linear_velocity.dot(global_basis.z)
 if before < 0.0 and z >= 0.0 and velocity > 0.05: crossed.emit(number, true)
 elif before > 0.0 and z <= 0.0 and velocity < -0.05: crossed.emit(number, false)
 previous[key] = z

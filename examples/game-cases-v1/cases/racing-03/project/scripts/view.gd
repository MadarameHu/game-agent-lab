extends Node3D

@export_group("Follow camera")
@export var target: Vehicle
@export var follow_response: float = 4.0
@export var zoom_response: float = 1.8
@export var near_distance: float = 10.0
@export var fast_distance: float = 19.0
@export var forward_lookahead: float = 3.5
@onready var camera = $Camera
var smoothed_speed: float = 0.0
var lookahead := Vector3.ZERO

func _physics_process(delta):
 if not is_instance_valid(target): return
 var velocity = target.sphere.linear_velocity
 var speed = Vector2(velocity.x, velocity.z).length()
 smoothed_speed = lerpf(smoothed_speed, speed, 1.0-exp(-2.5*delta))
 var factor = smoothstep(0.5, 8.0, smoothed_speed)
 var direction = Vector3(velocity.x, 0.0, velocity.z).normalized()
 lookahead = lookahead.lerp(direction * forward_lookahead * factor, 1.0-exp(-2.5*delta))
 global_position = global_position.lerp(target.get_vehicle_position()+lookahead, 1.0-exp(-follow_response*delta))
 camera.position.z = lerpf(camera.position.z, lerpf(near_distance, fast_distance, factor), 1.0-exp(-zoom_response*delta))

extends Node3D
signal completed(total: int)
const REQUIRED_COINS := 8
var at_goal := false
var level_completed := false
var completion_count := 0

func _ready() -> void:
    if RenderingServer.get_current_rendering_method() == "gl_compatibility":
        $Sun.light_energy = 0.24
        $Sun.shadow_opacity = 0.85
        $Environment.environment.background_energy_multiplier = 0.25
    var gate := Area3D.new()
    gate.name = "GoalArea"
    gate.collision_layer = 0
    gate.collision_mask = 1
    var shape_node := CollisionShape3D.new()
    var shape := CylinderShape3D.new()
    shape.radius = 1.15
    shape.height = 2.0
    shape_node.shape = shape
    shape_node.position.y = 0.5
    gate.add_child(shape_node)
    $World/flag.add_child(gate)
    gate.body_entered.connect(_on_goal_entered)
    gate.body_exited.connect(_on_goal_exited)
    $Player.coin_collected.connect(_on_coin_changed)
    $HUD.update_goal($Player.coins,false)

func _on_goal_entered(body: Node3D) -> void:
    if body != $Player or level_completed: return
    at_goal = true
    _evaluate_goal()

func _on_goal_exited(body: Node3D) -> void:
    if body != $Player or level_completed: return
    at_goal = false
    $HUD.update_goal($Player.coins,false)

func _on_coin_changed(_count: int) -> void:
    if level_completed: return
    $HUD.update_goal($Player.coins,at_goal)
    if at_goal: _evaluate_goal()

func _evaluate_goal() -> void:
    if level_completed: return
    if $Player.coins < REQUIRED_COINS:
        $HUD.update_goal($Player.coins,true)
        return
    level_completed = true
    completion_count += 1
    $Player.set_physics_process(false)
    $Player.velocity = Vector3.ZERO
    $Player/SoundFootsteps.stream_paused = true
    $Player/ParticlesTrail.emitting = false
    $Player/Character/AnimationPlayer.play("idle",0.1)
    $HUD.show_success($Player.coins)
    completed.emit($Player.coins)

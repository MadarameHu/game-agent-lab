extends Node

@export var stopped_speed: float = 0.5
var active: Vehicle
var view: Node3D
var motorcycle := true
var hud: Label
var notice: Label
var notice_seconds := 0.0
var switch_pending := false
const TRUCK = preload("res://scenes/vehicle.tscn")
const BIKE = preload("res://scenes/vehicle-motorcycle.tscn")

func _ready():
 active = get_parent().get_node("Vehicle")
 view = get_parent().get_node("View")
 var layer = CanvasLayer.new()
 add_child(layer)
 var panel = PanelContainer.new()
 panel.position = Vector2(22, 22)
 panel.custom_minimum_size = Vector2(330, 112)
 var style = StyleBoxFlat.new()
 style.bg_color = Color(0.025, 0.08, 0.12, 0.9)
 style.content_margin_left = 18; style.content_margin_right = 18
 style.content_margin_top = 12; style.content_margin_bottom = 12
 panel.add_theme_stylebox_override("panel", style)
 layer.add_child(panel)
 var box = VBoxContainer.new();panel.add_child(box)
 hud = Label.new();hud.add_theme_font_size_override("font_size",24);box.add_child(hud)
 var hint = Label.new();hint.text = "WASD drive  |  TAB switch when stopped";box.add_child(hint)
 notice = Label.new();notice.modulate = Color(1,0.78,0.35);box.add_child(notice)
 refresh_hud()

func refresh_hud():
 hud.text = "MOTORCYCLE" if motorcycle else "YELLOW TRUCK"

func _process(delta):
 notice_seconds = maxf(0.0, notice_seconds-delta)
 if notice_seconds == 0.0: notice.text = ""

func _unhandled_key_input(event):
 if event is InputEventKey and event.pressed and not event.echo and (event.physical_keycode == KEY_TAB or event.keycode == KEY_TAB):
  get_viewport().set_input_as_handled()
  if not switch_pending:
   switch_pending = true
   call_deferred("try_switch")

func try_switch():
 switch_pending = false
 if not is_instance_valid(active): return
 if active.sphere.linear_velocity.length() >= stopped_speed or absf(active.linear_speed) >= 0.08:
  notice.text = "Stop first to switch vehicle"
  notice_seconds = 2.5
  return
 var body_position = active.sphere.global_position
 var heading = active.vehicle_model.global_basis
 var old = active
 var replacement: Vehicle = (TRUCK if motorcycle else BIKE).instantiate()
 # Detach immediately so old body, input, effects and sound are inactive this frame.
 old.set_physics_process(false)
 old.sphere.freeze = true
 get_parent().remove_child(old)
 replacement.name = "Vehicle"
 replacement.position = body_position - Vector3(0,0.5,0)
 get_parent().add_child(replacement)
 replacement.sphere.global_position = body_position
 replacement.sphere.linear_velocity = Vector3.ZERO
 replacement.sphere.angular_velocity = Vector3.ZERO
 replacement.vehicle_model.global_position = body_position - Vector3(0,0.65,0)
 replacement.vehicle_model.global_basis = heading
 replacement.raycast.position = replacement.sphere.position
 replacement.prev_position = replacement.vehicle_model.position
 active = replacement
 view.target = active
 motorcycle = not motorcycle
 old.queue_free()
 refresh_hud()
 notice.text = "Vehicle ready"
 notice_seconds = 1.5

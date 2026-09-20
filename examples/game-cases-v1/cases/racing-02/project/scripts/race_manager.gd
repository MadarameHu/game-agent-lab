extends Node
const CHECKPOINT = preload('res://scripts/checkpoint.gd')
const HUD = preload('res://scripts/race_hud.gd')
var car
var sphere
var gates: Array = []
var hud
var state := 'countdown'
var remaining := 3.0
var elapsed := 0.0
var next_gate := 1
var message := ''
var message_time := 0.0
var spawn_sphere: Transform3D
var spawn_container: Transform3D
func _ready():
 car = get_parent().get_node('Vehicle'); sphere = car.get_node('Sphere')
 spawn_sphere = sphere.transform
 spawn_container = car.get_node('Container').transform
 var grid = get_parent().get_node('GridMap')
 var definitions = [[0,Vector3i(0,0,0),Vector3(0,0,1)],[1,Vector3i(-1,0,2),Vector3(-1,0,0)],[2,Vector3i(-2,0,0),Vector3(0,0,-1)],[3,Vector3i(-1,0,-3),Vector3(1,0,0)]]
 for definition in definitions:
  var gate = Area3D.new(); gate.set_script(CHECKPOINT)
  gate.name = 'FinishGate' if definition[0] == 0 else 'Checkpoint%d' % definition[0]
  add_child(gate)
  gate.global_position = grid.to_global(grid.map_to_local(definition[1]))
  gate.setup(definition[0],sphere,definition[2]); gate.crossed.connect(_crossed); gates.append(gate)
 hud = CanvasLayer.new(); hud.set_script(HUD); add_child(hud)
 restart()
func restart():
 state = 'countdown'; remaining = 3.0; elapsed = 0.0; next_gate = 1; message = ''; message_time = 0
 sphere.freeze = true; sphere.linear_velocity = Vector3.ZERO; sphere.angular_velocity = Vector3.ZERO
 sphere.transform = spawn_sphere
 car.get_node('Container').transform = spawn_container
 car.linear_speed = 0; car.angular_speed = 0; car.acceleration = 0; car.input = Vector3.ZERO
 car.prev_position = car.get_node('Container').position
 car.controls_enabled = false
 for gate in gates:gate.reset_tracking()
func _unhandled_key_input(event):
 if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_R:restart()
func _physics_process(delta):
 if state == 'countdown':
  remaining = maxf(0,remaining-delta)
  if remaining <= 0.0001:state = 'running'; sphere.freeze = false; car.controls_enabled = true
 elif state == 'running':elapsed += delta
 message_time = maxf(0,message_time-delta)
 if message_time == 0:message = ''
 hud.update_display(state,remaining,elapsed,next_gate,message)
func _crossed(number,forward):
 if state != 'running':return
 if not forward:
  message = 'Wrong direction'; message_time = 2.0; return
 if number == next_gate:
  next_gate += 1; message = 'Checkpoint %d cleared' % number; message_time = 1.5
 elif number == 0 and next_gate == 4:
  state = 'finished'; car.controls_enabled = false
 else:
  message = 'Pass CP %d first' % next_gate if next_gate <= 3 else 'Return to the finish'; message_time = 2.0

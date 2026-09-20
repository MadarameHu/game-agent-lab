extends CanvasLayer
var panel: PanelContainer
var title: Label
var timer_label: Label
var state_label: Label
var note: Label
func _ready():
 panel = PanelContainer.new()
 panel.position = Vector2(22,22)
 panel.custom_minimum_size = Vector2(360,150)
 var style = StyleBoxFlat.new()
 style.bg_color = Color(0.04,0.09,0.12,0.9)
 style.content_margin_left = 18; style.content_margin_right = 18
 style.content_margin_top = 14; style.content_margin_bottom = 14
 style.corner_radius_top_left = 10; style.corner_radius_bottom_right = 10
 panel.add_theme_stylebox_override('panel',style)
 add_child(panel)
 var box = VBoxContainer.new(); panel.add_child(box)
 title = Label.new(); title.text = 'WOODLAND / TIME TRIAL'; title.add_theme_font_size_override('font_size',18); box.add_child(title)
 timer_label = Label.new(); timer_label.add_theme_font_size_override('font_size',32); box.add_child(timer_label)
 state_label = Label.new(); box.add_child(state_label)
 note = Label.new(); note.text = 'WASD drive   ·   R restart'; note.modulate = Color(0.6,0.8,0.8); box.add_child(note)
func update_display(state,remaining,elapsed,next_gate,message):
 if timer_label == null:return
 timer_label.text = '%06.2f s' % elapsed
 if state == 'countdown':state_label.text = 'READY  %d' % ceili(remaining)
 elif state == 'finished':state_label.text = 'FINISHED  ·  Personal lap complete'
 else:state_label.text = ('GO!  ·  ' if elapsed < 0.8 else '') + ('Next: CP %d / 3' % next_gate if next_gate <= 3 else 'Next: START / FINISH')
 note.text = (message if message else 'WASD drive   ·   R restart')

extends Control

func _on_coin_collected(coins):
	
	$Coins.text = str(coins)

func _ready():
	var help := Label.new()
	help.name = "ControlsHint"
	help.text = "WASD / left stick: move    SPACE / A: double jump\nArrows / right stick: camera    + - / triggers: zoom"
	help.position = Vector2(28, 640)
	help.add_theme_font_size_override("font_size", 20)
	help.add_theme_color_override("font_color", Color("fff4d8"))
	help.add_theme_color_override("font_shadow_color", Color(0.06, 0.05, 0.12, 0.95))
	help.add_theme_constant_override("shadow_offset_x", 2)
	help.add_theme_constant_override("shadow_offset_y", 2)
	help.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(help)

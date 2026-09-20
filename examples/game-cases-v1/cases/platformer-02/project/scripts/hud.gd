extends Control
var goal_label: Label
var restart_button: Button
var success_panel: PanelContainer

func _ready() -> void:
    goal_label = Label.new()
    goal_label.name = "GoalProgress"
    goal_label.position = Vector2(58,128)
    goal_label.add_theme_font_override("font",load("res://fonts/lilita_one_regular.ttf"))
    goal_label.add_theme_font_size_override("font_size",24)
    goal_label.add_theme_color_override("font_color",Color("fff3bd"))
    goal_label.add_theme_color_override("font_shadow_color",Color("33243d"))
    goal_label.add_theme_constant_override("shadow_offset_x",2)
    goal_label.add_theme_constant_override("shadow_offset_y",2)
    add_child(goal_label)
    update_goal(0,false)

func _on_coin_collected(coins: int) -> void:
    $Coins.text = str(coins)+" / 8"

func update_goal(coins: int,near_flag: bool) -> void:
    $Coins.text = str(coins)+" / 8"
    if near_flag and coins<8:
        goal_label.text = "NEED %d MORE COINS\nKeep exploring, then return!" % (8-coins)
    elif coins<8:
        goal_label.text = "COLLECT 8 COINS\nThen reach the purple flag"
    else:
        goal_label.text = "GOAL UNLOCKED\nReach the purple flag!"

func show_success(coins: int) -> void:
    if is_instance_valid(success_panel): return
    goal_label.text = "COURSE COMPLETE"
    success_panel = PanelContainer.new()
    success_panel.name = "SuccessPanel"
    var style := StyleBoxFlat.new()
    style.bg_color = Color("29243f")
    style.corner_radius_top_left = 20
    style.corner_radius_top_right = 20
    style.corner_radius_bottom_left = 20
    style.corner_radius_bottom_right = 20
    style.content_margin_left = 30
    style.content_margin_right = 30
    style.content_margin_top = 28
    style.content_margin_bottom = 28
    success_panel.add_theme_stylebox_override("panel",style)
    add_child(success_panel)
    success_panel.set_anchors_preset(Control.PRESET_CENTER)
    success_panel.offset_left = -265
    success_panel.offset_right = 265
    success_panel.offset_top = -140
    success_panel.offset_bottom = 140
    var box := VBoxContainer.new()
    box.add_theme_constant_override("separation",20)
    success_panel.add_child(box)
    var title := Label.new()
    title.text = "COURSE COMPLETE!"
    title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    title.add_theme_font_override("font",load("res://fonts/lilita_one_regular.ttf"))
    title.add_theme_font_size_override("font_size",38)
    title.add_theme_color_override("font_color",Color("ffe69a"))
    box.add_child(title)
    var count := Label.new()
    count.text = "Collected %d / 14 coins" % coins
    count.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    count.add_theme_font_size_override("font_size",24)
    box.add_child(count)
    restart_button = Button.new()
    restart_button.name = "PlayAgain"
    restart_button.text = "PLAY AGAIN"
    restart_button.custom_minimum_size = Vector2(0,56)
    restart_button.add_theme_font_size_override("font_size",24)
    restart_button.pressed.connect(_restart)
    box.add_child(restart_button)
    restart_button.grab_focus()

func _restart() -> void:
    call_deferred("_reload")

func _reload() -> void:
    get_tree().reload_current_scene()

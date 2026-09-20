extends Node3D

@export var structures: Array[Structure] = []

var map:DataMap

var index:int = 0 # Index of structure being built

@export var selector:Node3D # The 'cursor'
@export var selector_container:Node3D # Node that holds a preview of the structure
@export var view_camera:Camera3D # Used for raycasting mouse
@export var gridmap:GridMap
@export var cash_display:Label

var plane:Plane # Used for raycasting mouse

func _ready():
	
	map = DataMap.new()
	plane = Plane(Vector3.UP, Vector3.ZERO)
	
	# Create new MeshLibrary dynamically, can also be done in the editor
	# See: https://docs.godotengine.org/en/stable/tutorials/3d/using_gridmaps.html
	
	var mesh_library = MeshLibrary.new()
	
	for structure in structures:
		
		var id = mesh_library.get_last_unused_item_id()
		
		mesh_library.create_item(id)
		mesh_library.set_item_mesh(id, get_mesh(structure.model))
		mesh_library.set_item_mesh_transform(id, Transform3D())
		
	gridmap.mesh_library = mesh_library
	
	map = load("res://sample map/map.res").duplicate(true)
	for cell in map.structures:
		gridmap.set_cell_item(Vector3i(cell.position.x, 0, cell.position.y), cell.structure, cell.orientation)
	setup_palette()
	update_structure()
	update_cash()

func _process(delta):
	
	# Controls
	
	action_rotate() # Rotates selection 90 degrees
	action_structure_toggle() # Toggles between structures
	
	action_save() # Saving
	action_load() # Loading
	action_load_resources() # Loading from resources
	
	# Map position based on mouse
	
	var world_position = plane.intersects_ray(
		view_camera.project_ray_origin(get_viewport().get_mouse_position()),
		view_camera.project_ray_normal(get_viewport().get_mouse_position()))

	# The pointer ray may not intersect the build plane (for example outside the window).
	if world_position == null:
		return

	var gridmap_position = Vector3(round(world_position.x), 0, round(world_position.z))
	selector.position = lerp(selector.position, gridmap_position, min(delta * 40, 1.0))
	
	# Building is handled only after GUI Controls have consumed their input.
	if not palette_panel.get_global_rect().has_point(get_viewport().get_mouse_position()):
		action_demolish(gridmap_position)

# Retrieve the mesh from a PackedScene, used for dynamically creating a MeshLibrary

func get_mesh(packed_scene):
	var scene_state:SceneState = packed_scene.get_state()
	for i in range(scene_state.get_node_count()):
		if(scene_state.get_node_type(i) == "MeshInstance3D"):
			for j in scene_state.get_node_property_count(i):
				var prop_name = scene_state.get_node_property_name(i, j)
				if prop_name == "mesh":
					var prop_value = scene_state.get_node_property_value(i, j)
					
					return prop_value.duplicate()

# Build (place) a structure

func action_build(gridmap_position):
	if Input.is_action_just_pressed("build") and not palette_panel.get_global_rect().has_point(get_viewport().get_mouse_position()):
		place_structure(gridmap_position)

func place_structure(gridmap_position):
	var previous_tile = gridmap.get_cell_item(gridmap_position)
	gridmap.set_cell_item(gridmap_position,index,gridmap.get_orthogonal_index_from_basis(selector.basis))
	if previous_tile != index:
		map.cash -= structures[index].price
		update_cash()
		Audio.play("sounds/placement-a.ogg",-20)

func _unhandled_input(event):
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var point = plane.intersects_ray(view_camera.project_ray_origin(event.position),view_camera.project_ray_normal(event.position))
		if point != null:
			place_structure(Vector3i(roundi(point.x),0,roundi(point.z)))
			get_viewport().set_input_as_handled()

# Demolish (remove) a structure

func action_demolish(gridmap_position):
	if Input.is_action_just_pressed("demolish"):
		if gridmap.get_cell_item(gridmap_position) != -1:
			gridmap.set_cell_item(gridmap_position, -1)
			
			Audio.play("sounds/removal-a.ogg, sounds/removal-b.ogg, sounds/removal-c.ogg, sounds/removal-d.ogg", -20)

# Rotates the 'cursor' 90 degrees

func action_rotate():
	if Input.is_action_just_pressed("rotate"):
		selector.rotate_y(deg_to_rad(90))
		
		Audio.play("sounds/rotate.ogg", -30)

# Toggle between structures to build

func action_structure_toggle():
	var previous_index = index
	if Input.is_action_just_pressed("structure_next"):
		index = wrap(index + 1, 0, structures.size())
		Audio.play("sounds/toggle.ogg", -30)
	
	if Input.is_action_just_pressed("structure_previous"):
		index = wrap(index - 1, 0, structures.size())
		Audio.play("sounds/toggle.ogg", -30)

	if index != previous_index:
		update_structure()

# Update the structure visual in the 'cursor'

func update_structure():
	# Clear previous structure preview in selector
	for n in selector_container.get_children():
		selector_container.remove_child(n)
		n.queue_free()
		
	# Create new structure preview in selector
	var _model = structures[index].model.instantiate()
	selector_container.add_child(_model)
	_model.position.y += 0.25
	refresh_palette()
	
func update_cash():
	cash_display.text = "$" + str(map.cash)
	refresh_palette()

# Saving/load

func action_save():
	if Input.is_action_just_pressed("save"):
		print("Saving map...")
		
		map.structures.clear()
		for cell in gridmap.get_used_cells():
			
			var data_structure:DataStructure = DataStructure.new()
			
			data_structure.position = Vector2i(cell.x, cell.z)
			data_structure.orientation = gridmap.get_cell_item_orientation(cell)
			data_structure.structure = gridmap.get_cell_item(cell)
			
			map.structures.append(data_structure)
			
		ResourceSaver.save(map, "user://map.res")
	
func action_load():
	if Input.is_action_just_pressed("load"):
		print("Loading map...")
		
		gridmap.clear()
		
		map = ResourceLoader.load("user://map.res")
		if not map:
			map = DataMap.new()
		for cell in map.structures:
			gridmap.set_cell_item(Vector3i(cell.position.x, 0, cell.position.y), cell.structure, cell.orientation)
			
		update_cash()

func action_load_resources():
	if Input.is_action_just_pressed("load_resources"):
		print("Loading map...")
		
		gridmap.clear()
		
		map = ResourceLoader.load("res://sample map/map.res")
		if not map:
			map = DataMap.new()
		for cell in map.structures:
			gridmap.set_cell_item(Vector3i(cell.position.x, 0, cell.position.y), cell.structure, cell.orientation)
			
		update_cash()

const STRUCTURE_NAMES = ["Straight road", "Road + lightposts", "Corner road", "Road split", "Intersection", "Pavement", "Fountain pavement", "Small house A", "Small house B", "Small house C", "Small house D", "Garage", "Grass", "Trees", "Tall trees"]
var palette_panel: PanelContainer
var palette_scroll: ScrollContainer
var palette_buttons: Dictionary = {}
var palette_status: Label
var palette_groups: Array[String] = []

func setup_palette():
	palette_panel = PanelContainer.new()
	palette_panel.name = "BuildPalette"
	palette_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	var background = StyleBoxFlat.new()
	background.bg_color = Color("edf1f8")
	background.corner_radius_top_left=10
	background.corner_radius_top_right=10
	background.corner_radius_bottom_left=10
	background.corner_radius_bottom_right=10
	background.content_margin_left=12
	background.content_margin_right=12
	background.content_margin_top=10
	background.content_margin_bottom=10
	palette_panel.add_theme_stylebox_override("panel",background)
	get_parent().get_node("CanvasLayer").add_child(palette_panel)
	var column = VBoxContainer.new()
	column.add_theme_constant_override("separation",7)
	palette_panel.add_child(column)
	var title = Label.new()
	title.text = "BUILD PALETTE"
	title.add_theme_font_size_override("font_size",19)
	title.add_theme_color_override("font_color",Color("26334c"))
	column.add_child(title)
	palette_status = Label.new()
	palette_status.add_theme_font_size_override("font_size",14)
	column.add_child(palette_status)
	palette_scroll = ScrollContainer.new()
	palette_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	palette_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(palette_scroll)
	var rows = VBoxContainer.new()
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_theme_constant_override("separation",3)
	palette_scroll.add_child(rows)
	var groups = {"ROADS":[0,1,2,3,4],"BUILDINGS":[7,8,9,10,11],"GROUND & LANDSCAPE":[5,6,12,13,14]}
	for group in groups:
		palette_groups.append(group)
		var heading = Label.new()
		heading.text=group
		heading.add_theme_font_size_override("font_size",12)
		heading.add_theme_color_override("font_color",Color("56637c"))
		heading.custom_minimum_size.y=23
		rows.add_child(heading)
		for item in groups[group]:
			var button = Button.new()
			button.name="Structure%d" % item
			button.toggle_mode=true
			button.focus_mode=Control.FOCUS_NONE
			button.mouse_filter=Control.MOUSE_FILTER_STOP
			button.alignment=HORIZONTAL_ALIGNMENT_LEFT
			button.custom_minimum_size.y=28
			button.add_theme_font_size_override("font_size",14)
			button.tooltip_text=structures[item].model.resource_path.get_file()+" | $"+str(structures[item].price)
			var normal = StyleBoxFlat.new()
			normal.bg_color=Color("dde4ef")
			normal.content_margin_left=8
			normal.content_margin_right=8
			normal.corner_radius_top_left=4
			normal.corner_radius_top_right=4
			normal.corner_radius_bottom_left=4
			normal.corner_radius_bottom_right=4
			button.add_theme_stylebox_override("normal",normal)
			var selected = normal.duplicate()
			selected.bg_color=Color("214f87")
			button.add_theme_stylebox_override("pressed",selected)
			var hover = normal.duplicate()
			hover.bg_color=Color("c8d7ee")
			button.add_theme_stylebox_override("hover",hover)
			button.add_theme_stylebox_override("hover_pressed",selected)
			button.pressed.connect(select_structure.bind(item))
			palette_buttons[item]=button
			rows.add_child(button)
	get_viewport().size_changed.connect(layout_palette)
	layout_palette()

func layout_palette():
	var viewport = get_viewport().get_visible_rect().size
	palette_panel.position=Vector2(viewport.x-280,78)
	palette_panel.size=Vector2(260,minf(660,viewport.y-108))

func select_structure(item: int):
	index=item
	update_structure()
	Audio.play("sounds/toggle.ogg",-30)

func refresh_palette():
	if not palette_status:return
	var price=structures[index].price
	var enough=map.cash>=price
	palette_status.text="%s  $%d\n%s" % [STRUCTURE_NAMES[index],price,"Can afford  |  Q / E cycle" if enough else "Need $%d more" % (price-map.cash)]
	palette_status.add_theme_color_override("font_color",Color("216544") if enough else Color("a92b37"))
	for item in palette_buttons:
		var button=palette_buttons[item]
		button.text="%s  $%d" % [STRUCTURE_NAMES[item],structures[item].price]
		button.set_pressed_no_signal(item==index)
		var affordable=map.cash>=structures[item].price
		button.add_theme_color_override("font_color",Color("26334c") if affordable else Color("a92b37"))
		button.add_theme_color_override("font_pressed_color",Color.WHITE if affordable else Color("ffb6be"))
	if palette_buttons.has(index): palette_scroll.ensure_control_visible(palette_buttons[index])

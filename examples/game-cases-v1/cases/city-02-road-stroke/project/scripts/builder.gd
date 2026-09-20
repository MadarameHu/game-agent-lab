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
	setup_road_ui()
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
	
	action_build(gridmap_position)
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
	if index < 5 or stroke_active:
		return
	if Input.is_action_just_pressed("build"):
		
		var previous_tile = gridmap.get_cell_item(gridmap_position)
		gridmap.set_cell_item(gridmap_position, index, gridmap.get_orthogonal_index_from_basis(selector.basis))
		
		if previous_tile != index:
			map.cash -= structures[index].price
			update_cash()
			
			Audio.play("sounds/placement-a.ogg, sounds/placement-b.ogg, sounds/placement-c.ogg, sounds/placement-d.ogg", -20)

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
		if stroke_active: refresh_road_preview()
		
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
		cancel_stroke()
		update_structure()
		update_road_status()

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
	
func update_cash():
	cash_display.text = "$" + str(map.cash)

# Saving/load

func action_save():
	if Input.is_action_just_pressed("save"):
		cancel_stroke()
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
		cancel_stroke()
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
		cancel_stroke()
		print("Loading map...")
		
		gridmap.clear()
		
		map = ResourceLoader.load("res://sample map/map.res")
		if not map:
			map = DataMap.new()
		for cell in map.structures:
			gridmap.set_cell_item(Vector3i(cell.position.x, 0, cell.position.y), cell.structure, cell.orientation)
			
		update_cash()

# Road strokes are staged in memory; GridMap changes only on mouse release.
var stroke_active := false
var stroke_cells: Array[Vector3i] = []
var last_stroke_cell := Vector3i.ZERO
var stroke_index := 0
var stroke_preview: Node3D
var road_status: Label
var road_message := ""

func setup_road_ui():
	stroke_preview = Node3D.new()
	stroke_preview.name = "RoadPreview"
	add_child(stroke_preview)
	road_status = Label.new()
	road_status.position = Vector2(24, 86)
	road_status.add_theme_color_override("font_color", Color("26334c"))
	road_status.add_theme_font_size_override("font_size", 18)
	road_status.mouse_filter = Control.MOUSE_FILTER_IGNORE
	get_parent().get_node("CanvasLayer").add_child(road_status)
	update_road_status()

func update_road_status():
	if not road_status: return
	var mode = "ROAD MODE  |  Drag LMB / Release to build / Esc cancel" if index < 5 else "SINGLE CELL  |  Click to build / RMB rotate / Q E select"
	road_status.text = mode + ("\n" + road_message if not road_message.is_empty() else "")

func road_cell(screen: Vector2):
	var point = plane.intersects_ray(view_camera.project_ray_origin(screen),view_camera.project_ray_normal(screen))
	if point == null: return null
	return Vector3i(roundi(point.x), 0, roundi(point.z))

func _unhandled_input(event):
	if event.is_action_pressed("ui_cancel") and stroke_active:
		cancel_stroke()
		road_message = "Cancelled — no cells changed, no money spent."
		update_road_status()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and index < 5:
			var cell = road_cell(event.position)
			if cell != null:
				begin_stroke(cell)
				get_viewport().set_input_as_handled()
		elif not event.pressed and stroke_active:
			var cell = road_cell(event.position)
			if cell != null: extend_stroke(cell)
			commit_stroke()
			get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion and stroke_active:
		var cell = road_cell(event.position)
		if cell != null: extend_stroke(cell)

func begin_stroke(cell: Vector3i):
	cancel_stroke()
	stroke_active = true
	stroke_index = index
	stroke_cells.append(cell)
	last_stroke_cell = cell
	refresh_road_preview()

func extend_stroke(cell: Vector3i):
	# Fill fast-pointer gaps deterministically, retaining visited cells only once.
	var cursor = last_stroke_cell
	while cursor != cell:
		if cursor.x != cell.x: cursor.x += 1 if cell.x > cursor.x else -1
		elif cursor.z != cell.z: cursor.z += 1 if cell.z > cursor.z else -1
		if not stroke_cells.has(cursor): stroke_cells.append(cursor)
	last_stroke_cell = cell
	refresh_road_preview()

func road_tile(cell: Vector3i) -> Vector2i:
	var orientation = gridmap.get_orthogonal_index_from_basis(selector.basis)
	if stroke_index > 1: return Vector2i(stroke_index, orientation)
	var north = stroke_cells.has(cell + Vector3i.FORWARD)
	var south = stroke_cells.has(cell + Vector3i.BACK)
	var east = stroke_cells.has(cell + Vector3i.RIGHT)
	var west = stroke_cells.has(cell + Vector3i.LEFT)
	var count = int(north) + int(south) + int(east) + int(west)
	if count >= 3: return Vector2i(4, 0)
	if (north or south) and (east or west):
		if south and west: return Vector2i(2, 0)
		if north and east: return Vector2i(2, 10)
		if south and east: return Vector2i(2, 16)
		return Vector2i(2, 22)
	if east or west: orientation = 22
	elif north or south: orientation = 0
	return Vector2i(stroke_index, orientation)

func stroke_info() -> Dictionary:
	var cost = 0
	var blocked = 0
	for cell in stroke_cells:
		var existing = gridmap.get_cell_item(cell)
		if existing >= 5: blocked += 1
		elif existing == -1: cost += structures[road_tile(cell).x].price
	return {"cost":cost,"blocked":blocked}

func refresh_road_preview():
	for child in stroke_preview.get_children():
		stroke_preview.remove_child(child)
		child.queue_free()
	var info = stroke_info()
	var invalid = info.blocked > 0 or info.cost > map.cash
	for cell in stroke_cells:
		var tile = road_tile(cell)
		var ghost = MeshInstance3D.new()
		ghost.mesh = gridmap.mesh_library.get_item_mesh(tile.x)
		ghost.basis = gridmap.get_basis_with_orthogonal_index(tile.y)
		ghost.position = Vector3(cell) + Vector3(0, 0.07, 0)
		var material = StandardMaterial3D.new()
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.albedo_color = Color(1,0.2,0.16,0.65) if invalid else Color(0.1,0.8,1,0.65)
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ghost.material_override = material
		stroke_preview.add_child(ghost)
	if info.blocked > 0: road_message = "Blocked: %d non-road cell(s). Entire stroke will stay unchanged. Esc to cancel." % info.blocked
	elif info.cost > map.cash: road_message = "Insufficient funds: $%d needed. Entire stroke will stay unchanged." % info.cost
	else: road_message = "%d unique cells | Cost $%d | Release to commit" % [stroke_cells.size(), info.cost]
	update_road_status()

func commit_stroke():
	if not stroke_active: return
	var info = stroke_info()
	if info.blocked > 0 or info.cost > map.cash:
		var reason = road_message
		cancel_stroke()
		road_message = reason
		update_road_status()
		return
	for cell in stroke_cells:
		if gridmap.get_cell_item(cell) == -1:
			var tile = road_tile(cell)
			gridmap.set_cell_item(cell, tile.x, tile.y)
	map.cash -= info.cost
	update_cash()
	var spent = info.cost
	cancel_stroke()
	road_message = "Road built. Spent $%d." % spent
	update_road_status()
	Audio.play("sounds/placement-a.ogg", -20)

func cancel_stroke():
	stroke_active = false
	stroke_cells.clear()
	if stroke_preview:
		for child in stroke_preview.get_children():
			stroke_preview.remove_child(child)
			child.queue_free()
	road_message = ""
	update_road_status()

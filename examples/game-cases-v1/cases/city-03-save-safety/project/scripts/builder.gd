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
	
	setup_save_ui()
	apply_map(load("res://sample map/map.res").duplicate(true))
	update_structure()
	show_notice("Official sample loaded. Ready to build.")

func _process(delta):
	if reset_dialog.visible:
		return
	
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
	if Input.is_action_just_pressed("build"):
		
		var previous_tile = gridmap.get_cell_item(gridmap_position)
		var previous_orientation = gridmap.get_cell_item_orientation(gridmap_position)
		gridmap.set_cell_item(gridmap_position, index, gridmap.get_orthogonal_index_from_basis(selector.basis))
		
		if previous_tile != index or previous_orientation != gridmap.get_cell_item_orientation(gridmap_position):
			dirty = true
			show_notice("Unsaved edits. F1 saves this city.")
		if previous_tile != index:
			map.cash -= structures[index].price
			update_cash()
			
			Audio.play("sounds/placement-a.ogg, sounds/placement-b.ogg, sounds/placement-c.ogg, sounds/placement-d.ogg", -20)

# Demolish (remove) a structure

func action_demolish(gridmap_position):
	if Input.is_action_just_pressed("demolish"):
		if gridmap.get_cell_item(gridmap_position) != -1:
			gridmap.set_cell_item(gridmap_position, -1)
			dirty = true
			show_notice("Unsaved edits. F1 saves this city.")
			
			Audio.play("sounds/removal-a.ogg, sounds/removal-b.ogg, sounds/removal-c.ogg, sounds/removal-d.ogg", -20)

# Rotates the 'cursor' 90 degrees

func action_rotate():
	if Input.is_action_just_pressed("rotate"):
		selector.rotate_y(deg_to_rad(90))
		
		Audio.play("sounds/rotate.ogg", -30)

# Toggle between structures to build

func action_structure_toggle():
	if Input.is_action_just_pressed("structure_next"):
		index = wrap(index + 1, 0, structures.size())
		Audio.play("sounds/toggle.ogg", -30)
	
	if Input.is_action_just_pressed("structure_previous"):
		index = wrap(index - 1, 0, structures.size())
		Audio.play("sounds/toggle.ogg", -30)

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
	
func update_cash():
	cash_display.text = "$" + str(map.cash)

# Saving/load


const SAVE_PATH = "user://map.res"
const TEMP_PATH = "user://map.pending.res"
var dirty := false
var status_label: Label
var reset_dialog: ConfirmationDialog

func setup_save_ui():
	status_label = Label.new()
	status_label.position = Vector2(24,86)
	status_label.add_theme_font_size_override("font_size",18)
	status_label.add_theme_color_override("font_color",Color("26334c"))
	status_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	get_parent().get_node("CanvasLayer").add_child(status_label)
	reset_dialog = ConfirmationDialog.new()
	reset_dialog.title = "Reload official sample?"
	reset_dialog.dialog_text = "Unsaved city changes will be discarded.\nYour saved file will not be changed."
	reset_dialog.ok_button_text = "Discard edits and reload"
	reset_dialog.cancel_button_text = "Keep current city"
	reset_dialog.confirmed.connect(reload_official_sample)
	reset_dialog.canceled.connect(func(): show_notice("Reload cancelled. Current city kept."))
	add_child(reset_dialog)

func show_notice(message: String, failed := false):
	status_label.text = message + "\nF1 Save  |  F2 Load  |  F3 Official sample" + ("  |  UNSAVED" if dirty else "")
	status_label.add_theme_color_override("font_color",Color("8b2525") if failed else Color("26334c"))

func capture_map() -> DataMap:
	var snapshot = DataMap.new()
	snapshot.cash = map.cash
	for cell in gridmap.get_used_cells():
		var item = DataStructure.new()
		item.position = Vector2i(cell.x,cell.z)
		item.orientation = gridmap.get_cell_item_orientation(cell)
		item.structure = gridmap.get_cell_item(cell)
		snapshot.structures.append(item)
	return snapshot

func validate_map(candidate: Resource) -> String:
	if not candidate is DataMap: return "Not a supported city save."
	var positions = {}
	for cell in candidate.structures:
		if cell == null: return "Save contains an empty structure entry."
		if cell.structure < 0 or cell.structure >= structures.size(): return "Save contains an unknown structure type."
		if cell.orientation < 0 or cell.orientation >= 24: return "Save contains an invalid rotation."
		if positions.has(cell.position): return "Save contains duplicate grid positions."
		positions[cell.position] = true
	return ""

func apply_map(candidate: DataMap):
	# Caller has validated the entire resource before this commit point.
	gridmap.clear()
	map = candidate.duplicate(true)
	for cell in map.structures:
		gridmap.set_cell_item(Vector3i(cell.position.x,0,cell.position.y),cell.structure,cell.orientation)
	dirty = false
	update_cash()

func save_city() -> bool:
	var snapshot = capture_map()
	var err = ResourceSaver.save(snapshot,TEMP_PATH)
	if err != OK:
		show_notice("Save failed: cannot write temporary file (error %d). City kept." % err,true)
		return false
	# Replace only after the complete resource has been written successfully.
	err = DirAccess.rename_absolute(ProjectSettings.globalize_path(TEMP_PATH),ProjectSettings.globalize_path(SAVE_PATH))
	if err != OK:
		show_notice("Save failed: cannot replace save file (error %d). City kept." % err,true)
		return false
	dirty = false
	show_notice("Saved successfully to user://map.res.")
	return true

func load_city() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		show_notice("Load failed: no saved city yet. Press F1 to save. Current city kept.",true)
		return false
	# Ignore both top-level and nested resource cache to read the latest disk state.
	var candidate = ResourceLoader.load(SAVE_PATH,"",ResourceLoader.CACHE_MODE_IGNORE_DEEP)
	if candidate == null:
		show_notice("Load failed: save is corrupt or unreadable. Current city kept.",true)
		return false
	var problem = validate_map(candidate)
	if not problem.is_empty():
		show_notice("Load failed: " + problem + " Current city kept.",true)
		return false
	apply_map(candidate)
	show_notice("Loaded latest saved city successfully.")
	return true

func reload_official_sample():
	var candidate = ResourceLoader.load("res://sample map/map.res","",ResourceLoader.CACHE_MODE_IGNORE_DEEP)
	var problem = validate_map(candidate)
	if not problem.is_empty():
		show_notice("Sample reload failed: " + problem + " Current city kept.",true)
		return
	apply_map(candidate)
	show_notice("Official sample reloaded. Saved file unchanged.")

func action_save():
	if Input.is_action_just_pressed("save"): save_city()

func action_load():
	if Input.is_action_just_pressed("load"): load_city()

func action_load_resources():
	if Input.is_action_just_pressed("load_resources"):
		if dirty: reset_dialog.popup_centered(Vector2i(480,180))
		else: reload_official_sample()

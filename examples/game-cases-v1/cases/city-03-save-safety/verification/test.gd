extends SceneTree
var checks=[]
var b
func check(id,okay,summary,details={}): checks.append({"id":id,"pass":okay,"summary":summary,"details":details})
func state():
 var cells={}
 for p in b.gridmap.get_used_cells():cells[str(p)]=[b.gridmap.get_cell_item(p),b.gridmap.get_cell_item_orientation(p)]
 return {"cash":b.map.cash,"cells":cells}
func act(action,method):
 Input.action_press(action);b.call(method);Input.action_release(action)
func build(cell,item,orientation):
 b.index=item;b.update_structure();b.selector.basis=b.gridmap.get_basis_with_orthogonal_index(orientation)
 Input.action_press("build");b.action_build(cell);Input.action_release("build")
func _initialize():call_deferred("run")
func run():
 root.size=Vector2i(1280,900)
 change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
 await process_frame;await process_frame
 b=current_scene.get_node("Builder");b.set_process(false)
 var initial=state();var official=load("res://sample map/map.res");var exact=true
 for cell in official.structures:
  var p=Vector3i(cell.position.x,0,cell.position.y)
  exact=exact and b.gridmap.get_cell_item(p)==cell.structure and b.gridmap.get_cell_item_orientation(p)==cell.orientation
 var no_save=not FileAccess.file_exists("user://map.res")
 check("startup",exact and initial.cells.size()==122 and initial.cash==5860 and no_save and b.status_label.mouse_filter==Control.MOUSE_FILTER_IGNORE,"Exact122-cell official startup,5860cash,no save pre-created,nonblocking status",{"user_directory":OS.get_user_data_dir()})
 act("load","action_load")
 var missing=state()==initial and b.status_label.text.contains("no saved city")
 build(Vector3i(10,0,2),7,10)
 var first=state();act("save","action_save")
 var save1=b.status_label.text.contains("Saved successfully") and not b.dirty
 var cached=ResourceLoader.load("user://map.res")
 await process_frame
 build(Vector3i(11,0,4),8,22)
 Input.action_press("demolish");b.action_demolish(Vector3i(10,0,2));Input.action_release("demolish")
 var second=state();act("save","action_save")
 var save2=b.status_label.text.contains("Saved successfully") and not b.dirty
 await process_frame
 build(Vector3i(12,0,5),14,0)
 act("load","action_load")
 var latest=state()==second and b.status_label.text.contains("Loaded latest") and not b.dirty
 check("latest-save",save1 and save2 and first!=second and latest and cached.cash==first.cash,"Two real ResourceSaver writes; F2 bypasses deliberately retained old cached resource; exact second positions/items/rotations/cash restored",{"first_cash":first.cash,"second_cash":second.cash,"loaded_cash":b.map.cash,"cached_old_cash":cached.cash})
 await process_frame
 build(Vector3i(12,0,5),13,16)
 var current=state();var old_saved_hash=FileAccess.get_sha256("user://map.res")
 DirAccess.make_dir_absolute("user://map.pending.res")
 var failed=not b.save_city()
 var save_failure=failed and b.status_label.text.contains("Save failed") and b.dirty and state()==current and FileAccess.get_sha256("user://map.res")==old_saved_hash
 DirAccess.remove_absolute("user://map.pending.res")
 check("save-failure",save_failure,"Unwritable temporary target reports failure; city,dirty flag and existing saved bytes preserved")
 var corrupt=FileAccess.open("user://map.res",FileAccess.WRITE);corrupt.store_string("not a Godot resource");corrupt.close()
 act("load","action_load")
 var bad_bytes=state()==current and b.status_label.text.contains("corrupt or unreadable")
 var invalid=b.capture_map();invalid.structures[0].structure=99
 ResourceSaver.save(invalid,"user://map.res")
 act("load","action_load")
 var bad_type=state()==current and b.status_label.text.contains("unknown structure")
 check("failed-load-preserves",missing and bad_bytes and bad_type,"Missing/corrupt/invalid structure saves preserve entire grid and cash with specific explanations",{"missing":missing,"corrupt":bad_bytes,"invalid_type":bad_type})
 var before_reset=state();var saved_hash=FileAccess.get_sha256("user://map.res")
 act("load_resources","action_load_resources")
 var prompt=b.reset_dialog.visible and state()==before_reset
 b.reset_dialog.get_cancel_button().pressed.emit()
 await process_frame
 print("CANCELSTATE ",state()==before_reset," dirty ",b.dirty," visible ",b.reset_dialog.visible," message ",b.status_label.text)
 var cancel=state()==before_reset and b.dirty and b.status_label.text.contains("cancelled") and not b.reset_dialog.visible
 await process_frame
 act("load_resources","action_load_resources")
 b.reset_dialog.get_ok_button().pressed.emit()
 var confirm=state()==initial and not b.dirty and FileAccess.get_sha256("user://map.res")==saved_hash
 check("sample-reset",prompt and cancel and confirm,"F3 displays confirmation for unsaved changes; actual dialog button signals cancel/confirm preserve or restore correctly; user save untouched",{"prompt":prompt,"cancel":cancel,"confirm":confirm})
 var f=FileAccess.open(OS.get_cmdline_user_args()[0].path_join("behavior.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks},"  "))
 var okay=true
 for c in checks:okay=okay and c["pass"]
 print("BEHAVIOR "+JSON.stringify(checks));quit(0 if okay else 1)

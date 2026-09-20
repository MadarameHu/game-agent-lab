extends SceneTree
var checks=[]
var b
func check(id,okay,summary,details={}):checks.append({"id":id,"pass":okay,"summary":summary,"details":details})
func state():
 var cells={}
 for p in b.gridmap.get_used_cells():cells[str(p)]=[b.gridmap.get_cell_item(p),b.gridmap.get_cell_item_orientation(p)]
 return {"cash":b.map.cash,"cells":cells}
func mouse(cell,pressed):
 var e=InputEventMouseButton.new()
 e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed;e.position=b.view_camera.unproject_position(Vector3(cell));e.global_position=e.position
 root.push_input(e,true)
func motion(cell):
 var e=InputEventMouseMotion.new()
 e.position=b.view_camera.unproject_position(Vector3(cell));e.global_position=e.position;e.button_mask=MOUSE_BUTTON_MASK_LEFT
 root.push_input(e,true)
func escape():
 var e=InputEventKey.new();e.keycode=KEY_ESCAPE;e.pressed=true;root.push_input(e,true)
 var u=InputEventKey.new();u.keycode=KEY_ESCAPE;u.pressed=false;root.push_input(u,true)
func _initialize():call_deferred("run")
func run():
 root.size=Vector2i(1280,900)
 change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
 for i in range(100):await process_frame
 b=current_scene.get_node("Builder");b.set_process(false);current_scene.get_node("View").set_process(false)
 b.view_camera.position=Vector3(0,0,60)
 current_scene.get_node("View").position=Vector3(1,0,1)
 print("SCREEN ",root.size," POINT ",b.view_camera.unproject_position(Vector3(10,0,0))," raycell ",b.road_cell(b.view_camera.unproject_position(Vector3(10,0,0))))
 var initial=state();var original=load("res://sample map/map.res");var exact=true
 for cell in original.structures:
  var p=Vector3i(cell.position.x,0,cell.position.y)
  exact=exact and b.gridmap.get_cell_item(p)==cell.structure and b.gridmap.get_cell_item_orientation(p)==cell.orientation
 check("startup",exact and initial.cells.size()==122 and initial.cash==5860 and b.road_status.text.contains("ROAD MODE"),"122 unchanged original cells,5860 cash,visible road mode")
 mouse(Vector3i(10,0,0),true)
 print("DOWN ", b.stroke_active, " ", b.stroke_cells)
 motion(Vector3i(12,0,0));motion(Vector3i(12,0,2));motion(Vector3i(12,0,0))
 print("PATH ",b.stroke_cells)
 var preview=b.stroke_active and b.stroke_cells.size()==5 and b.stroke_preview.get_child_count()==5 and state()==initial
 var corner_preview=b.road_tile(Vector3i(12,0,0))==Vector2i(2,0)
 mouse(Vector3i(12,0,0),false)
 var built=b.gridmap.get_used_cells().size()==127 and b.map.cash==5735 and b.gridmap.get_cell_item(Vector3i(12,0,0))==2 and b.gridmap.get_cell_item_orientation(Vector3i(12,0,0))==0
 check("stroke-preview-commit",preview and corner_preview and built and not b.stroke_active,"Mouse drag turns and revisits:5 unique ghosts, no mutation before release,one125 charge,auto corner",{"preview":preview,"corner_preview":corner_preview,"built":built,"cash":b.map.cash})
 var before=state()
 mouse(Vector3i(10,0,3),true);motion(Vector3i(12,0,3));escape();mouse(Vector3i(12,0,3),false)
 var cancelled=state()==before and not b.stroke_active and b.stroke_preview.get_child_count()==0
 var house=Vector3i.ZERO
 for cell in original.structures:
  if cell.structure>=7 and cell.structure<=10:house=Vector3i(cell.position.x,0,cell.position.y);break
 mouse(Vector3i(10,0,3),true);motion(house)
 var conflict=b.road_status.text.contains("Blocked") and b.stroke_info().blocked>0 and state()==before
 mouse(house,false)
 var refused=state()==before
 mouse(house,true);escape();mouse(house,false)
 check("stroke-cancel-conflict",cancelled and conflict and refused and state()==before,"Esc preserves complete grid/cash; house conflict visible and whole stroke refused",{"cancelled":cancelled,"conflict_visible":conflict,"refused":refused})
 b.index=6
 Input.action_press("structure_next");b.action_structure_toggle();Input.action_release("structure_next")
 var selected=b.index==7 and b.road_status.text.contains("SINGLE CELL")
 var basis=b.selector.basis
 Input.action_press("rotate");b.action_rotate();Input.action_release("rotate")
 var rotated=not b.selector.basis.is_equal_approx(basis)
 var cash=b.map.cash;var count=b.gridmap.get_used_cells().size()
 Input.action_press("build");b.action_build(Vector3i(10,0,5));Input.action_release("build")
 var house_built=b.gridmap.get_cell_item(Vector3i(10,0,5))==7 and b.map.cash==cash-b.structures[7].price and b.gridmap.get_used_cells().size()==count+1
 await process_frame
 b.index=12;b.update_structure();cash=b.map.cash
 Input.action_press("build");b.action_build(Vector3i(11,0,5));Input.action_release("build")
 check("single-build-controls",selected and rotated and house_built and b.gridmap.get_cell_item(Vector3i(11,0,5))==12 and b.map.cash==cash-b.structures[12].price,"Q/E mode switch,right rotation,house and grass single-cell placement retained")
 var f=FileAccess.open(OS.get_cmdline_user_args()[0].path_join("behavior.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks},"  "))
 var okay=true
 for c in checks:okay=okay and c["pass"]
 print("BEHAVIOR "+JSON.stringify(checks));quit(0 if okay else 1)

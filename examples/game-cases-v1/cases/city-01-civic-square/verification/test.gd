extends SceneTree
var checks = []
var b
func check(id, okay, summary, details = {}):
 checks.append({"id":id,"pass":okay,"summary":summary,"details":details})
func press(action):
 Input.action_press(action)
func release(action):
 Input.action_release(action)
func _initialize(): call_deferred("run")
func run():
 change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
 await process_frame
 await process_frame
 b = current_scene.get_node("Builder")
 b.set_process(false)
 var official = load("res://sample map/map.res")
 check("startup", b.gridmap.get_used_cells().size() == 149 and b.map.cash == 5860, "Direct startup loads149 cells and unchanged5860 balance")
 var preserved = true
 var old = {}
 for cell in official.structures:
  var p = Vector3i(cell.position.x,0,cell.position.y)
  old[p]=true
  preserved = preserved and b.gridmap.get_cell_item(p)==cell.structure and b.gridmap.get_cell_item_orientation(p)==cell.orientation
 check("original-cells",preserved and old.size()==122,"All122 original cells and orientations preserved")
 var additions = {}; var types = {}; var in_bounds = true
 for p in b.gridmap.get_used_cells():
  if not old.has(p):
   additions[p]=true
   types[b.gridmap.get_cell_item(p)]=true
   in_bounds=in_bounds and p.x>=3 and p.x<=8 and p.z>=6 and p.z<=10
 var reached = {}; var queue = [Vector3i(6,0,6)]
 while not queue.is_empty():
  var p = queue.pop_front()
  if reached.has(p) or not additions.has(p):continue
  reached[p]=true
  for d in [Vector3i.LEFT,Vector3i.RIGHT,Vector3i.FORWARD,Vector3i.BACK]:queue.append(p+d)
 check("layout",in_bounds and reached.size()==additions.size() and types.has(7) and types.has(8) and types.has(5) and types.has(12) and types.has(13) and types.has(14) and b.gridmap.get_cell_item(Vector3i(6,0,5))<5,"27 connected additions, two house types, layered planting and paved entry",{"added":additions.size(),"connected":reached.size()})
 b.index=6
 press("structure_next");b.action_structure_toggle();release("structure_next")
 var selected = b.index==7
 press("rotate");b.action_rotate();release("rotate")
 var ori = b.gridmap.get_orthogonal_index_from_basis(b.selector.basis)
 var cash = b.map.cash
 var target = Vector3i(12,0,9)
 press("build");b.action_build(target);release("build")
 var built = b.gridmap.get_cell_item(target)==7 and b.gridmap.get_cell_item_orientation(target)==ori and b.map.cash==cash-b.structures[7].price
 press("demolish");b.action_demolish(target);release("demolish")
 var removed = b.gridmap.get_cell_item(target)==-1
 press("load_resources");b.action_load_resources();release("load_resources")
 check("build-controls",selected and ori!=0 and built and removed and b.gridmap.get_used_cells().size()==122 and b.map.cash==5860,"Q/E selection,90-degree rotation,build with exact charge,demolish,F3 sample reset")
 var f=FileAccess.open(OS.get_cmdline_user_args()[0].path_join("behavior.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"checks":checks},"  "))
 var okay=true
 for c in checks:okay=okay and c["pass"]
 print("BEHAVIOR "+JSON.stringify(checks))
 quit(0 if okay else 1)

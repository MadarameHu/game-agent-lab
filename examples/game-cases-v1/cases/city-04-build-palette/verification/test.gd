extends SceneTree
var checks=[]
var b
func check(id,okay,summary,details={}):checks.append({"id":id,"pass":okay,"summary":summary,"details":details})
func state():
 var cells={}
 for p in b.gridmap.get_used_cells():cells[str(p)]=[b.gridmap.get_cell_item(p),b.gridmap.get_cell_item_orientation(p)]
 return {"cash":b.map.cash,"cells":cells}
func click(position):
 var motion=InputEventMouseMotion.new();motion.position=position;motion.global_position=position;root.push_input(motion,true)
 for pressed in [true,false]:
  var event=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event.position=position;event.global_position=position
  root.push_input(event,true)
func _initialize():call_deferred("run")
func run():
 root.size=Vector2i(1280,900)
 change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
 for i in range(5):await process_frame
 b=current_scene.get_node("Builder");b.set_process(false);current_scene.get_node("View").set_process(false)
 b.view_camera.position=Vector3(0,0,60);current_scene.get_node("View").position=Vector3(1,0,1)
 var initial=state();var official=load("res://sample map/map.res");var exact=true
 for cell in official.structures:
  var p=Vector3i(cell.position.x,0,cell.position.y)
  exact=exact and b.gridmap.get_cell_item(p)==cell.structure and b.gridmap.get_cell_item_orientation(p)==cell.orientation
 check("startup",exact and initial.cells.size()==122 and initial.cash==5860,"Exact122 official cells and5860 starting cash")
 var prices=[25,25,25,25,25,10,10,50,60,70,70,70,10,25,25]
 var content=b.palette_buttons.size()==15 and b.palette_groups==["ROADS","BUILDINGS","GROUND & LANDSCAPE"]
 for i in range(15):
  var button=b.palette_buttons[i]
  content=content and button.text.contains("$"+str(prices[i])) and b.structures[i].price==prices[i] and button.tooltip_text.contains(b.structures[i].model.resource_path.get_file())
 check("palette-content",content,"All15 original models/prices present in3groups; tooltip links name to real model filename")
 var clicks=true;var clicked=[]
 for i in range(15):
  b.palette_scroll.ensure_control_visible(b.palette_buttons[i])
  await process_frame;await process_frame
  var position=b.palette_buttons[i].get_global_rect().get_center()
  click(position)
  await process_frame
  clicks=clicks and b.index==i and b.palette_buttons[i].button_pressed and state()==initial
  clicked.append({"index":i,"selected":b.index,"unchanged":state()==initial})
 var target=Vector3i(-4,0,-5)
 var before=b.gridmap.get_used_cells().size();var empty=b.gridmap.get_cell_item(target)==-1
 b.select_structure(7)
 var screen=b.view_camera.unproject_position(Vector3(target))
 var outside=not b.palette_panel.get_global_rect().has_point(screen)
 click(screen)
 var built=b.gridmap.get_cell_item(target)==7 and b.gridmap.get_used_cells().size()==before+1 and b.map.cash==5860-50
 check("gui-no-clickthrough",clicks and empty and outside and built,"15 actual viewport GUI clicks only select; outside GUI a world click still builds and charges",{"buttons":clicked,"world_click":built})
 var synced=true
 for n in range(15):
  var expected=(b.index+1)%15
  Input.action_press("structure_next");b.action_structure_toggle();Input.action_release("structure_next")
  var selected_count=0
  for i in b.palette_buttons:
   if b.palette_buttons[i].button_pressed:selected_count+=1
  synced=synced and b.index==expected and b.palette_buttons[expected].button_pressed and selected_count==1 and b.selector_container.get_child(0).scene_file_path==b.structures[expected].model.resource_path
  await process_frame
 var expected_previous=wrapi(b.index-1,0,15)
 Input.action_press("structure_previous");b.action_structure_toggle();Input.action_release("structure_previous")
 synced=synced and b.index==expected_previous and b.palette_buttons[expected_previous].button_pressed and b.selector_container.get_child(0).scene_file_path==b.structures[expected_previous].model.resource_path
 check("keyboard-preview-sync",synced,"All15 next steps plus previous:one highlighted item, original index order,and corresponding3D model")
 var cash=b.map.cash;b.map.cash=0;b.update_cash()
 var unaffordable=b.palette_status.text.contains("Need $")
 for i in b.palette_buttons:unaffordable=unaffordable and b.palette_buttons[i].get_theme_color("font_color")==Color("a92b37")
 b.map.cash=cash;b.update_cash()
 var affordable=b.palette_status.text.contains("Can afford")
 var sizes=[];var compact=true
 for size in [Vector2i(1280,900),Vector2i(1024,768)]:
  root.size=size;b.layout_palette();await process_frame
  var rect=b.palette_panel.get_global_rect()
  compact=compact and rect.size.x<=float(size.x)*0.3 and rect.position.x>=0 and rect.end.x<=size.x and rect.end.y<=size.y
  sizes.append({"viewport":str(size),"panel":str(rect)})
 check("affordability-layout",unaffordable and affordable and compact,"Injected zero-balance fixture shows need and red prices; balance restore refreshes. Panel<=30%width at two sizes",{"unaffordable":unaffordable,"affordable":affordable,"sizes":sizes})
 var f=FileAccess.open(OS.get_cmdline_user_args()[0].path_join("behavior.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks},"  "))
 var okay=true
 for c in checks:okay=okay and c["pass"]
 print("BEHAVIOR "+JSON.stringify(checks));quit(0 if okay else 1)

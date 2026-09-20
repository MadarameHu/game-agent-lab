extends SceneTree
func v3(v): return [v.x,v.y,v.z]
func v2(v): return [v.x,v.z]
func _initialize(): call_deferred("inspect")
func inspect():
 var scene=load("res://scenes/main.tscn").instantiate()
 root.add_child(scene)
 var grid=scene.get_node("GridMap")
 var lib=grid.mesh_library
 var car=scene.get_node("Vehicle")
 var report={"scene_loaded":true,"grid_scale":v3(grid.scale),"grid_position":v3(grid.position),"cell_size":v3(grid.cell_size),"vehicle_root":v3(car.global_position),"physical_spawn":v3(car.get_node("Sphere").global_position),"forward":v3(car.get_node("Container").global_basis.z),"spawn_cell":v3(grid.local_to_map(grid.to_local(car.global_position))),"cells":[],"nodes":[]}
 for cell in grid.get_used_cells():
  var id=grid.get_cell_item(cell)
  var basis=grid.get_cell_item_basis(cell)
  var center=grid.map_to_local(cell)
  var aabb=lib.get_item_mesh(id).get_aabb()
  var bounds=[]
  for i in range(8): bounds.append(v3(grid.to_global(center+basis*aabb.get_endpoint(i))))
  var corners=[]
  for x in [-5.0,5.0]:
   for z in [-5.0,5.0]:corners.append(v3(grid.to_global(center+basis*Vector3(x,0,z))))
  var ports=[]
  if id in [4,6]:
   for port in [Vector3(0,0,-1),Vector3(0,0,1)]:ports.append(v3(basis*port))
  elif id==3:
   for port in [Vector3(-1,0,0),Vector3(0,0,1)]:ports.append(v3(basis*port))
  report.cells.append({"cell":v3(cell),"id":id,"name":lib.get_item_name(id),"orientation":grid.get_cell_item_orientation(cell),"center":v3(grid.to_global(center)),"ports":ports,"bounds_world":bounds,"tile_corners_world":corners})
 var queue=[scene]
 while not queue.is_empty():
  var node=queue.pop_front()
  var desc={"path":str(scene.get_path_to(node)),"type":node.get_class(),"script":node.get_script().resource_path if node.get_script()!=null else null}
  if node is Node3D:desc["transform"]=str(node.transform)
  report.nodes.append(desc)
  queue.append_array(node.get_children())
 var file=FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
 file.store_string(JSON.stringify(report,"  "));file.close()
 scene.queue_free();quit()

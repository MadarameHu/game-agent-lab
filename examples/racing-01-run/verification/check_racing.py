#!/usr/bin/env python3
"""Independent fixed-contract GridMap topology, decoration and physical-lap verifier."""
import argparse, collections, hashlib, json, math, re, shutil, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROAD_IDS={3,4,6}
PLANAR={0,10,16,22}
def distance(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def point_segment(p,a,b):
 d=(b[0]-a[0],b[1]-a[1]);q=d[0]*d[0]+d[1]*d[1]
 t=max(0,min(1,((p[0]-a[0])*d[0]+(p[1]-a[1])*d[1])/q)) if q else 0
 return distance(p,(a[0]+t*d[0],a[1]+t*d[1]))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def segments_intersect(a,b,c,d):
 ab=(b[0]-a[0],b[1]-a[1]);cd=(d[0]-c[0],d[1]-c[1]);den=cross(ab,cd)
 if abs(den)<1e-9:return False
 ac=(c[0]-a[0],c[1]-a[1]);t=cross(ac,cd)/den;u=cross(ac,ab)/den
 return 0<=t<=1 and 0<=u<=1

def point_inside(p,polygon):
 inside=False
 for a,b in zip(polygon,polygon[1:]+polygon[:1]):
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside

def rect_segment_distance(rect,a,b):
 x0,z0,x1,z1=rect
 if any(x0<=p[0]<=x1 and z0<=p[1]<=z1 for p in [a,b]):return 0
 cs=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
 if any(segments_intersect(a,b,c,d) for c,d in zip(cs,cs[1:]+cs[:1])):return 0
 vals=[point_segment(c,a,b) for c in cs]
 vals.extend(math.hypot(max(x0-p[0],0,p[0]-x1),max(z0-p[1],0,p[1]-z1)) for p in [a,b])
 return min(vals)

def normalized_main(text):
 # Freeze every byte outside the GridMap data dictionary.
 match=re.search(r'(\[node name="GridMap"[^\n]*\]\n)(.*?)(?=\n\[node|\Z)',text,re.S)
 if not match:raise ValueError('GridMap node missing')
 body=re.sub(r'data\s*=\s*\{.*?\n\}', 'data = <ALLOWED_GRIDMAP_CELLS>',match.group(2),flags=re.S)
 return text[:match.start(2)]+body+text[match.end(2):]

def geometry(meta):
 errors=[];cells={tuple(int(x) for x in c['cell']):c for c in meta['cells']}
 roads={k:c for k,c in cells.items() if c['id'] in ROAD_IDS}
 unsupported=[c for c in cells.values() if c['name'].startswith('track-') and c['id'] not in ROAD_IDS]
 if unsupported:errors.append('Unsupported road items: '+str([c['id'] for c in unsupported]))
 if not roads:return {'closed_track':False,'errors':['No roads']},None
 ports={}
 for k,c in roads.items():
  if c['orientation'] not in PLANAR or k[1]!=0:errors.append(f'Nonplanar road {k}')
  ports[k]=[tuple(int(round(x)) for x in p) for p in c['ports']]
  if len(ports[k])!=2:errors.append(f'Tile needs two ports {k}')
 adjacency={k:[] for k in roads}
 for k,ps in ports.items():
  for p in ps:
   neighbor=tuple(a+b for a,b in zip(k,p));opposite=tuple(-a for a in p)
   if neighbor not in roads or opposite not in ports.get(neighbor,[]):errors.append(f'Unmatched port {k}->{neighbor}')
   else:adjacency[k].append(neighbor)
 start=tuple(int(x) for x in meta['spawn_cell'])
 if start not in roads:errors.append('Spawn cell is not a road')
 visited=set();queue=[next(iter(roads))]
 while queue:
  k=queue.pop()
  if k not in visited:visited.add(k);queue.extend(adjacency[k])
 if len(visited)!=len(roads):errors.append('Roads have disconnected components')
 if errors:return {'closed_track':False,'errors':errors,'road_count':len(roads)},None
 forward=meta['forward'];neighbors=adjacency[start]
 successor=max(neighbors,key=lambda p:(p[0]-start[0])*forward[0]+(p[2]-start[2])*forward[2])
 if (successor[0]-start[0])*forward[0]+(successor[2]-start[2])*forward[2]<.5:errors.append('Spawn cannot enter cycle along original forward heading')
 order=[start];prev=start;current=successor
 while current!=start and len(order)<=len(roads):
  order.append(current);nxt=[k for k in adjacency[current] if k!=prev]
  if len(nxt)!=1:errors.append('Ambiguous route');break
  prev,current=current,nxt[0]
 if len(order)!=len(roads) or current!=start:errors.append('Route does not visit every road exactly once')
 # Each tile's true curved or straight centerline, inferred only from its port geometry.
 points=[];point_tiles=[];turns=[]
 for i,k in enumerate(order):
  prev=order[i-1];nxt=order[(i+1)%len(order)];cell=roads[k]
  entry=(prev[0]-k[0],prev[2]-k[2]);exit=(nxt[0]-k[0],nxt[2]-k[2])
  incoming=(-entry[0],-entry[1]);signed=incoming[1]*exit[0]-incoming[0]*exit[1];turns.append(signed)
  cx,_,cz=cell['center'];h=3.75
  if cell['id']==3:
   ox,oz=cx+(entry[0]+exit[0])*h,cz+(entry[1]+exit[1])*h
   a0=math.atan2(-exit[1],-exit[0]);a1=math.atan2(-entry[1],-entry[0]);da=(a1-a0+math.pi)%(2*math.pi)-math.pi
   tilepoints=[(ox+h*math.cos(a0+da*j/20),oz+h*math.sin(a0+da*j/20)) for j in range(21)]
  else:
   a=(cx+entry[0]*h,cz+entry[1]*h);b=(cx+exit[0]*h,cz+exit[1]*h)
   tilepoints=[(a[0]+(b[0]-a[0])*j/25,a[1]+(b[1]-a[1])*j/25) for j in range(26)]
  for p in tilepoints:
   if not points or distance(points[-1],p)>.02:points.append(p);point_tiles.append(i)
 # Remove overlap across closing seam; rotate in fixed forward direction at spawn.
 if distance(points[0],points[-1])<.02:points.pop();point_tiles.pop()
 spawn=(meta['physical_spawn'][0],meta['physical_spawn'][2])
 start_indices=[i for i,t in enumerate(point_tiles) if t==0]
 idx=min(start_indices,key=lambda i:distance(points[i],spawn))
 points=points[idx:]+points[:idx];point_tiles=point_tiles[idx:]+point_tiles[:idx]
 points.append(points[0]);point_tiles.append(point_tiles[0])
 plain=[roads[k]['id']==6 for k in order]
 straight=any(all((plain*2)[i+j] for j in range(3)) for i in range(len(plain)))
 s_pairs=[i for i in range(len(turns)) if turns[i]>0 and turns[(i+1)%len(turns)]<0]
 spawn_distance=min(point_segment(spawn,a,b) for a,b in zip(points,points[1:]))
 bounds_ok=all(abs(p[0])<=30.01 and abs(p[2])<=30.01 for c in roads.values() for p in c['tile_corners_world'])
 self_cross=[]
 # Nonadjacent centerline segments must not cross (endpoint seams ignored).
 for i,(a,b) in enumerate(zip(points,points[1:])):
  for j in range(i+2,len(points)-1):
   if i==0 and j==len(points)-2:continue
   c,d=points[j:j+2]
   if segments_intersect(a,b,c,d):self_cross.append([i,j])
 if self_cross:errors.append('Centerline self-intersects')
 forests=[c for c in cells.values() if c['id']==1];tents=[c for c in cells.values() if c['id']==2]
 decor_results=[]
 for cell in forests+tents:
  xs=[p[0] for p in cell['bounds_world']];zs=[p[2] for p in cell['bounds_world']];rect=(min(xs),min(zs),max(xs),max(zs))
  clearance=min(rect_segment_distance(rect,a,b) for a,b in zip(points,points[1:]))
  corners=[(rect[0],rect[1]),(rect[2],rect[1]),(rect[2],rect[3]),(rect[0],rect[3])]
  outside=not any(point_inside(c,points[:-1]) for c in corners)
  decor_results.append({'cell':cell['cell'],'name':cell['name'],'world_aabb_xz':rect,'distance_to_centerline':clearance,'overlaps_road_band':clearance<3.375-.02,'all_aabb_corners_outside_route':outside})
 no_decor_overlap=all(not d['overlaps_road_band'] for d in decor_results)
 tents_outside=bool(tents) and all(d['all_aabb_corners_outside_route'] and not d['overlaps_road_band'] for d in decor_results if d['name']=='decoration-tents')
 report={'closed_track':not errors,'errors':errors,'road_count':len(roads),'ordered_cells':[list(k) for k in order],'turn_signs_left_positive':turns,'plain_three_straights':straight,'adjacent_left_right_indices':s_pairs,'required_geometry':straight and bool(s_pairs) and any(c['id']==4 for c in roads.values()),'finish_tiles':sum(c['id']==4 for c in roads.values()),'spawn_centerline_distance_m':spawn_distance,'spawn_on_road':spawn_distance<=2.5,'roads_inside_original_floor':bounds_ok,'forest_count':len(forests),'tents_count':len(tents),'decor_clear_of_road_band':no_decor_overlap,'tents_aabbs_outside':tents_outside,'decoration_geometry':decor_results,'spawn_and_decor':spawn_distance<=2.5 and bounds_ok and bool(forests) and tents_outside and no_decor_overlap,'road_band_half_width_m':3.375,'decor_note':'Conservative transformed mesh AABB versus sampled true centerline band; includes empty mesh corners. Camera visibility remains human pending.','route_length_m':sum(distance(a,b) for a,b in zip(points,points[1:])),'self_intersections':self_cross}
 route={'points':points,'point_tile_indices':point_tiles,'order':[list(k) for k in order],'direction':'from original spawn forward +Z','spacing_max_m':.3,'corner_radius_m':3.75,'seam_overlap_tolerance_m':.02,'derived_from':'actual runtime GridMap items/ports; no execution-agent plan read'}
 return report,route

def run_command(command,log,timeout=60):
 started=time.monotonic()
 with log.open('w') as f:
  try:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,text=True,timeout=timeout);code=p.returncode;timed=False
  except subprocess.TimeoutExpired:code=None;timed=True
 return {'command':command,'exit_code':code,'timed_out':timed,'wall_seconds':time.monotonic()-started,'log':log.name}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--godot',type=Path,required=True);ap.add_argument('--drive',action='store_true');ap.add_argument('--baseline-project',type=Path,default=HERE.parent.parent/'game-inputs-v1/bases/racing/project');a=ap.parse_args()
 a.project=a.project.resolve();a.out=a.out.resolve();a.godot=a.godot.resolve()
 if a.out.exists() and any(a.out.iterdir()):raise SystemExit('Refusing nonempty output directory: evidence must be fresh for every invocation')
 a.out.mkdir(parents=True,exist_ok=True)
 scratch=HERE.parents[2]/'work/racing-01/validator/cases'/a.out.name
 # Never edit the supplied project; import a fresh isolated snapshot.
 scratch.mkdir(parents=True,exist_ok=True);snapshot=scratch/('project_'+str(time.time_ns()))
 shutil.copytree(a.project,snapshot,ignore=shutil.ignore_patterns('.godot','.git'))
 snapshot_main_hash=hashlib.sha256((snapshot/'scenes/main.tscn').read_bytes()).hexdigest()
 shutil.copy2(snapshot/'scenes/main.tscn',a.out/'source-main.tscn')
 protected=json.loads((HERE.parent/'contract/protected-files.json').read_text())
 differences=[p for p,h in protected.items() if not (a.project/p).is_file() or hashlib.sha256((a.project/p).read_bytes()).hexdigest()!=h]
 main_unchanged=normalized_main((a.project/'scenes/main.tscn').read_text())==normalized_main((a.baseline_project/'scenes/main.tscn').read_text())
 commands=[]
 commands.append(run_command([str(a.godot),'--headless','--editor','--import','--quit','--path',str(snapshot)],a.out/'import.log'))
 commands.append(run_command([str(a.godot),'--headless','--path',str(snapshot),'--quit-after','5','--script',str(HERE/'inspect_scene.gd'),'--',str(a.out/'scene_metadata.json')],a.out/'inspect.log'))
 meta=json.loads((a.out/'scene_metadata.json').read_text()) if (a.out/'scene_metadata.json').exists() else None
 error_lines=[line for name in ['import.log','inspect.log'] for line in (a.out/name).read_text().splitlines() if ('SCRIPT ERROR' in line or 'ERROR:' in line) and 'leaked at exit' not in line and 'resources still in use at exit' not in line]
 load_good=bool(meta) and all(c['exit_code']==0 and not c['timed_out'] for c in commands) and not error_lines
 report,route=geometry(meta) if meta else ({'closed_track':False,'errors':['Failed to load runtime scene']},None)
 (a.out/'topology.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 if route:(a.out/'route.json').write_text(json.dumps(route,indent=2))
 lap=None
 if a.drive and report['closed_track'] and route:
  commands.append(run_command([str(a.godot),'--headless','--path',str(snapshot),'--fixed-fps','60','--quit-after','18100','--script',str(HERE/'drive_lap.gd'),'--',str(a.out/'route.json'),str(a.out)],a.out/'drive.log'))
  lap=json.loads((a.out/'lap.json').read_text()) if (a.out/'lap.json').exists() else {'passed':False,'status':'driver_no_result'}
 snapshot_hash_matches_source=snapshot_main_hash==hashlib.sha256((a.project/'scenes/main.tscn').read_bytes()).hexdigest()
 checks={'project_loads':load_good,'protected_gameplay':not differences and main_unchanged and snapshot_hash_matches_source,'closed_track':report.get('closed_track',False),'required_geometry':report.get('required_geometry',False),'spawn_and_decor':report.get('spawn_and_decor',False),'physical_lap':bool(lap and lap.get('passed') and lap.get('physics_hz')==60 and commands[-1]['exit_code']==0 and not commands[-1]['timed_out'])}
 result={'checks':checks,'engine_reward':int(all(checks.values())),'human_review':None,'combined_reward':None,'resource_or_script_errors':error_lines,'protected_file_differences':differences,'main_outside_gridmap_unchanged':main_unchanged,'physical_lap_status':lap.get('status') if lap else 'not_run','source_main_sha256':hashlib.sha256((a.project/'scenes/main.tscn').read_bytes()).hexdigest(),'snapshot_main_sha256':snapshot_main_hash,'snapshot_main_matches_source':snapshot_hash_matches_source,'driver_sha256':hashlib.sha256((HERE/'drive_lap.gd').read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256((HERE.parent/'contract/acceptance.json').read_bytes()).hexdigest(),'snapshot':str(snapshot),'commands':commands,'note':'Failure of one bounded input-only test driver is not proof that a human cannot drive the course.'}
 (a.out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

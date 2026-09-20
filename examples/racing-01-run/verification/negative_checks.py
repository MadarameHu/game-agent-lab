"""Geometry-only negative controls, using metadata copies and no product edits."""
import copy, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('checker',HERE/'check_racing.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
source=HERE.parent/'evidence/final-verification-v2/scene_metadata.json'
if not source.exists():source=HERE.parents[2]/'work/racing-01/validator/dev002/scene_metadata.json'
meta=json.loads(source.read_text());results=[]
bad=copy.deepcopy(meta);road=next(c for c in bad['cells'] if c['id']==6);bad['cells'].remove(road);r,_=checker.geometry(bad);assert not r['closed_track'];results.append({'case':'remove_one_road_tile','expected':'closed_track false','observed':r['closed_track'],'errors':r['errors'],'passed':True})
bad=copy.deepcopy(meta)
for c in bad['cells']:
 if c['id']==4:c.update(id=6,name='track-straight')
r,_=checker.geometry(bad);assert r['closed_track'] and not r['required_geometry'] and r['finish_tiles']==0;results.append({'case':'replace_finish_with_plain_straight','expected':'closed loop still valid, required_geometry false','observed':{'closed_track':r['closed_track'],'required_geometry':r['required_geometry'],'finish_tiles':r['finish_tiles']},'passed':True})
# An 18-cell rectangular cycle has four same-signed turns, ample straight tiles, one finish.
order=[(0,0),(0,1),(0,2),(0,3),(-1,3),(-2,3),(-3,3),(-3,2),(-3,1),(-3,0),(-3,-1),(-3,-2),(-3,-3),(-2,-3),(-1,-3),(0,-3),(0,-2),(0,-1)]
bad=copy.deepcopy(meta);bad['cells']=[c for c in bad['cells'] if c['id'] not in checker.ROAD_IDS]
corner_orient={frozenset([(-1,0),(0,1)]):0,frozenset([(1,0),(0,-1)]):10,frozenset([(1,0),(0,1)]):16,frozenset([(-1,0),(0,-1)]):22}
for i,(x,z) in enumerate(order):
 p=order[i-1];n=order[(i+1)%len(order)];ports=[(p[0]-x,p[1]-z),(n[0]-x,n[1]-z)];straight=ports[0][0]==-ports[1][0] and ports[0][1]==-ports[1][1]
 item=4 if (x,z)==(0,0) else (6 if straight else 3);orientation=(0 if ports[0][0]==0 else 16) if straight else corner_orient[frozenset(ports)]
 cx,cz=(x+.5)*7.4925,(z+.5)*7.4925;bounds=[[cx+dx,-.125,cz+dz] for dx in [-3.75,3.75] for dz in [-3.75,3.75]]
 bad['cells'].append({'cell':[x,0,z],'id':item,'name':{3:'track-corner',4:'track-finish',6:'track-straight'}[item],'orientation':orientation,'center':[cx,-.125,cz],'ports':[[p[0],0,p[1]] for p in ports],'tile_corners_world':bounds,'bounds_world':bounds})
r,_=checker.geometry(bad);assert r['closed_track'] and r['plain_three_straights'] and r['finish_tiles']==1 and not r['adjacent_left_right_indices'] and not r['required_geometry']
results.append({'case':'valid_rectangle_without_adjacent_opposite_turns','expected':'closed_track true, straights true, finish present, required_geometry false','observed':{'closed_track':r['closed_track'],'plain_three_straights':r['plain_three_straights'],'turns':r['turn_signs_left_positive'],'required_geometry':r['required_geometry']},'passed':True})
out={'metadata_source':str(source),'product_mutated':False,'tests':results};(HERE/'negative-control-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))

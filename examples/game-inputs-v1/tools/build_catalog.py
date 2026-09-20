#!/usr/bin/env python3
"""Assemble authored task briefs with pinned source references; no task solutions."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES={'platformer':'平台跳跃','city-builder':'城市建造','racing':'赛车'}
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def main():
 tasks=[];bases=[]
 for base_id,name in NAMES.items():
  b=ROOT/'bases'/base_id;source=json.loads((b/'source.json').read_text());briefs=json.loads((b/'briefs.json').read_text())
  assert len(briefs)==4
  bases.append({'id':base_id,'name':name,'source':f'bases/{base_id}/source.json','readme':f'bases/{base_id}/README.md','preview':f'previews/{base_id}/scene.png','task_count':4})
  for brief in briefs:
   for asset in brief['available_assets']:
    assert (b/'project'/asset).exists(),f'Missing {base_id}: {asset}'
   task={**brief,'schema_version':1,'base_id':base_id,'base_name':name,'status':'input_ready_task_not_executed',
    'query_origin':'Authored for this collection; not an upstream dataset annotation',
    'initial_project':f'bases/{base_id}/project','scene_setup':'city-sample' if base_id=='city-builder' else 'default',
    'source_manifest':f'bases/{base_id}/source.json','source_manifest_sha256':hashlib.sha256((b/'source.json').read_bytes()).hexdigest(),
    'preview':f'previews/{base_id}/scene.png','path_conventions':{'initial_project':'relative to collection root','available_assets':'relative to initial_project','editable_paths':'relative to initial_project; annotations specify new files or restrictions'},
    'evaluation_status':'Acceptance notes are human-authored task requirements, not implemented automatic checkers.'}
   if base_id=='city-builder':
    task['initial_state']['startup']='Use the collection launcher to load the official sample resource automatically; opening upstream project directly requires F3. The adapter populates existing GridMap and cash from that resource without implementing the query.'
   folder=ROOT/'tasks'/task['id'];write(folder/'task.json',task)
   body=f"# {task['title']}\n\n任务ID：`{task['id']}` · 类型：{task['category']} · 难度：{task['difficulty']}\n\n## 用户需求\n\n{task['query']}\n\n## 初始状态\n\n"
   initial=task['initial_state'];body+=(json.dumps(initial,ensure_ascii=False,indent=2) if not isinstance(initial,str) else initial)+'\n\n'
   for title,key in [('可用素材与代码资源','available_assets'),('允许修改范围','editable_paths'),('需要保留','required_preservation'),('交付审阅要点（尚未实现自动校验器）','acceptance_notes')]:
    body+='## '+title+'\n\n'+'\n'.join('- '+x for x in task[key])+'\n\n'
   body+=f"## 使用\n\n本任务从共享基础工程 `{task['initial_project']}` 开始，资源路径均相对于该工程。\n\n在集合根目录运行：\n\n```bash\npython3 tools/inputs.py play {task['id']}\npython3 tools/inputs.py prepare {task['id']} --dest /absolute/path/to/new-workspace\n```\n\n这里只准备初始输入；需求尚未执行。修改前请复制到独立目录，保留共享基线。\n"
   (folder/'QUERY.md').write_text(body)
   tasks.append(task)
 assert len({t['id'] for t in tasks})==12
 write(ROOT/'catalog.json',{'schema_version':1,'title':'游戏任务输入库 · 第一批','bases':bases,'tasks':tasks})
 print('Assembled',len(tasks),'task packets from',len(bases),'pinned bases')
if __name__=='__main__':main()

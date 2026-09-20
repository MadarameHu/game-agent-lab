#!/usr/bin/env python3
"""Inspect or launch fixed input scenes; prepare isolated task workspaces."""
from pathlib import Path
import argparse, json, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]

def config():
    p=ROOT/'runtime.json'
    r=json.loads(p.read_text())
    if not Path(r['godot']).is_file():
        raise ValueError('Godot executable not found; update runtime.json godot path')
    return r

def task(task_id):
    if not task_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in task_id):
        raise ValueError('Invalid task ID')
    p=ROOT/'tasks'/task_id/'task.json'
    return json.loads(p.read_text())

def project_for(task_id):
    t=task(task_id)
    p=(ROOT/t['initial_project']).resolve()
    if not p.is_relative_to(ROOT) or not (p/'project.godot').is_file():
        raise ValueError('Invalid project path')
    return p,t

def ensure_import(project):
    if (project/'.godot/global_script_class_cache.cfg').exists():return
    cmd=[config()['godot'],'--headless','--editor','--import','--path',str(project),'--rendering-method','gl_compatibility','--quit']
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    (project.parent/'last-import.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode or 'SCRIPT ERROR:' in result.stderr:
        raise ValueError('Import failed; inspect last-import.log')

def command(task_id, mode='play'):
    p,t=project_for(task_id)
    ensure_import(p)
    cmd=[config()['godot'],'--path',str(p),'--rendering-method','gl_compatibility']
    if mode=='editor':cmd+=['--editor']
    elif mode=='play':cmd+=['--script',str(ROOT/'tools/capture_preview.gd'),'--','--scene-setup',t['scene_setup']]
    return cmd

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['list','play','editor','prepare','preview'])
    ap.add_argument('task_id',nargs='?')
    ap.add_argument('--dest',help='New destination directory for prepare mode')
    a=ap.parse_args()
    if a.mode=='list':
        for p in sorted((ROOT/'tasks').glob('*/task.json')):
            t=json.loads(p.read_text());print(t['id']+'  '+t['title'])
        return
    p,t=project_for(a.task_id)
    if a.mode=='prepare':
        if not a.dest:ap.error('prepare requires --dest PATH')
        dest=Path(a.dest).expanduser().resolve()
        if dest.exists():raise ValueError('Destination exists; refusing overwrite')
        if dest==ROOT or dest.is_relative_to(ROOT/'bases'):raise ValueError('Keep task workspaces outside bases')
        shutil.copytree(p,dest,ignore=shutil.ignore_patterns('.godot','.git'))
        shutil.copy2(ROOT/'tasks'/t['id']/'task.json',dest/'TASK.json')
        shutil.copy2(ROOT/'tasks'/t['id']/'QUERY.md',dest/'QUERY.md')
        meta=dest/'.input';meta.mkdir()
        shutil.copy2(ROOT/'tools/capture_preview.gd',meta/'start.gd')
        shutil.copy2(ROOT/t['source_manifest'],meta/'source.json')
        patches=ROOT/'bases'/t['base_id']/'patches'
        if patches.exists():shutil.copytree(patches,meta/'patches')
        starter = '''#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys
P=Path(__file__).resolve().parent
G=os.environ.get("GODOT", GODOT_PLACEHOLDER)
if not (P/".godot").exists():
    subprocess.run([G,"--headless","--editor","--import","--path",str(P),"--rendering-method","gl_compatibility","--quit"],check=True,timeout=60)
cmd=[G,"--path",str(P),"--rendering-method","gl_compatibility"]
if "--check" in sys.argv: cmd += ["--headless","--quit-after","180"]
cmd += ["--script",str(P/".input/start.gd"),"--","--scene-setup", SETUP_PLACEHOLDER]
raise SystemExit(subprocess.call(cmd))
'''.replace('GODOT_PLACEHOLDER',repr(config()['godot'])).replace('SETUP_PLACEHOLDER',repr(t['scene_setup']))
        (dest/'START_INPUT.py').write_text(starter)
        print('Prepared initial project; requested change has NOT been implemented:',dest)
        print('Launch the exact initial state: python3',dest/'START_INPUT.py')
    elif a.mode=='preview':
        out=ROOT/'previews'/t['base_id']
        out.mkdir(parents=True,exist_ok=True)
        cmd=command(a.task_id,'capture')+['--resolution','1200x800','--script',str(ROOT/'tools/capture_preview.gd'),'--','--preview-out',str(out),'--scene-setup',t['scene_setup']]
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'native.log').write_text(proc.stdout+'\n'+proc.stderr)
        (out/'execution.json').write_text(json.dumps({'command':cmd,'exit_code':proc.returncode},indent=2)+'\n')
        print(proc.stdout,proc.stderr)
        raise SystemExit(proc.returncode)
    else:
        raise SystemExit(subprocess.call(command(a.task_id,a.mode)))
if __name__=='__main__':
    main()

"use strict";
let current = null;
const selectedRun = new URLSearchParams(window.location.search).get("run_id");
const $ = id => document.getElementById(id);
const names = {scene_load:"场景结构与加载", bounds:"房间边界", no_overlap:"物体重叠", route_exists:"角色通路", rollout_reaches_goal:"真实物理到达"};
const subtitles = {scene_load:"合法资产、固定角色与目标、至少 6 个物体",bounds:"碰撞体位于房间内",no_overlap:"检测容差见引擎原始诊断",route_exists:"Godot 物理探测 + 网格路径搜索",rollout_reaches_goal:"CharacterBody3D 实际移动至目标半径内"};
const statusNames = {running:"运行中",awaiting_human:"等待你的审阅",accepted:"已接受",rejected:"已拒绝"};
function json(value){return JSON.stringify(value,null,2);}
function node(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
function fileUrl(path){return "/run-file/"+encodeURIComponent(current.manifest.run_id)+"/"+path.split("/").map(encodeURIComponent).join("/");}
function origin(candidate){return candidate?.origin==="model"?"真实模型输出":candidate?.origin==="fixture"?"人工 fixture · 非模型生成":"来源未记录";}
function image(id,candidate){const box=$(id);box.replaceChildren();if(candidate?.screenshot){const img=node("img");img.src=fileUrl(candidate.screenshot);img.alt=origin(candidate)+"场景总览";img.onerror=()=>box.replaceChildren(node("span","截图尚未生成"));box.append(img);}else box.append(node("span","截图尚未生成"));}
function pill(check){return node("span",check?check.pass?"● 通过":"● 未通过":"—", "pill "+(check?check.pass?"pass":"fail":"pending"));}
function expand(title,value){const d=node("details");d.append(node("summary",title),node("pre",typeof value==="string"?value:json(value)));return d;}
function draw(data){current=data;const m=data.manifest;const first=data.candidates[0],last=data.candidates.find(c=>c.id===m.final_candidate_id)||data.candidates.at(-1);$("status").textContent=statusNames[m.status]||m.status;$("brief").textContent=m.brief;$("run-id").textContent=m.run_id;$("model-name").textContent=m.model?.name||"未记录";$("call-count").textContent=Number.isInteger(m.model_call_count)?`${m.model_call_count} 次`:"未记录";$("provenance").textContent=json(m.model||{});$("candidate-count").textContent=`${data.candidates.length} 个候选 · 所有失败均保留`;$("initial-origin").textContent=origin(first);$("final-origin").textContent=origin(last);image("initial-image",first);image("final-image",last);$("initial-caption").textContent=first?`${first.id} · ${first.checks_data?.hard_pass?"全部硬检查通过":"包含未通过检查"}`:"等待场景";$("final-caption").textContent=last?`${last.id} · ${last.checks_data?.hard_pass?"全部硬检查通过":"等待修复或检查"}`:"等待候选";$("reward").textContent=`引擎奖励 ${last?.checks_data?.engine_reward??"—"}`;
const gates=$("gates");gates.replaceChildren();for(const id of Object.keys(names)){const r=node("div",undefined,"gate-row"),label=node("div",names[id]);label.append(node("small",subtitles[id]));r.append(label,pill(data.candidates.length>1?first?.checks_data?.checks?.find(c=>c.id===id):null),pill(last?.checks_data?.checks?.find(c=>c.id===id)));gates.append(r);}const diag=$("diagnostics");diag.replaceChildren();for(const c of data.candidates){diag.append(expand(`${c.id} · ${origin(c)}`,c.checks_data||"尚未完成"));}
const reviewed=!!m.human_review;$("accept").disabled=!data.can_accept;$("reject").disabled=m.status!=="awaiting_human"||reviewed;$("play").disabled=!m.final_candidate_id;$("comment").disabled=reviewed;$("comment").value=m.human_review?.comment||$("comment").value;$("accept-hint").textContent=reviewed?"审阅已落盘；验收截图与检查证据保持原样。":data.can_accept?"全部硬检查已通过，等待你独立判断。":"最终硬检查未全部通过，当前不能接受。";$("review-state").textContent=reviewed?`${m.human_review.decision==="accept"?"你已接受":"你已拒绝"} · ${m.human_review.comment||"未填写评论"}`:"尚未提交人类审阅；组合奖励为空，SFT 样本不会提前生成。";
const trace=$("timeline");trace.replaceChildren();data.trajectory.forEach((event,i)=>{const row=node("div",undefined,"timeline-item"),d=node("details"),s=node("summary");s.append(node("span",event.type||event.event||`事件 ${i+1}`),node("time",event.timestamp||event.time||""));d.append(s,node("pre",json(event)));row.append(node("span",String(i+1).padStart(2,"0"),"timeline-num"),d);trace.append(row);});if(!data.trajectory.length)trace.append(node("p","轨迹尚未写入。","muted"));const a=$("artifacts");a.replaceChildren();for(const artifact of data.artifacts)a.append(expand(artifact.path,artifact.text));}
function renderCaseMode(data){
  const single=data.candidates.length===1;
  const comparison=document.querySelector(".comparison");
  comparison.classList.toggle("single",single);
  comparison.querySelector(".scene-card").hidden=single;
  $("scene-section-title").textContent=single?"从需求生成的场景":"从初始状态到最终候选";
  $("final-card-title").textContent=single?"模型生成结果":"02 / 最终候选";
  document.querySelector(".verification").classList.toggle("single-result",single);
  $("candidate-count").textContent=single?"1 次候选生成 · 未经历修复":`${data.candidates.length} 个候选 · 所有失败均保留`;
}
async function navigation(){try{const response=await fetch("/api/runs");if(!response.ok)return;const runs=await response.json();const nav=$("run-navigation");nav.replaceChildren();nav.append(node("span","查看案例","nav-label"));for(const run of runs){const a=node("a",`${run.display_label} · ${run.run_id}`,current?.manifest.run_id===run.run_id?"active":"");a.href="/?run_id="+encodeURIComponent(run.run_id);if(current?.manifest.run_id===run.run_id)a.setAttribute("aria-current","page");nav.append(a);}}catch{}}
async function load(){try{const r=await fetch("/api/run"+(selectedRun?"?run_id="+encodeURIComponent(selectedRun):"")),d=await r.json();if(!r.ok)throw Error(d.error);draw(d);renderCaseMode(d);await navigation();}catch(e){$("status").textContent="等待运行";notify(e.message,true);}}
function notify(text,error=false){$("notice").textContent=text;$("notice").classList.toggle("error",error);}
async function post(action,extra={}){if(!current)return;try{const r=await fetch("/api/"+action,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({run_id:current.manifest.run_id,...extra})}),d=await r.json();if(!r.ok)throw Error(d.error);notify(d.message||(action==="review"?"你的审阅已保存，训练导出已更新。":"完成"));if(action==="review")await load();}catch(e){notify(e.message,true);}}
$("accept").addEventListener("click",()=>post("review",{decision:"accept",comment:$("comment").value}));$("reject").addEventListener("click",()=>post("review",{decision:"reject",comment:$("comment").value}));$("play").addEventListener("click",()=>post("play"));load();setInterval(()=>{if(!current||current.manifest.status==="running")load();},5000);

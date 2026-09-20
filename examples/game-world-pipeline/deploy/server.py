"""Single-worker isolated Qwen service; model only emits text, never executes it."""
import os
GPU = os.environ.get("GAME_MODEL_GPU")
MODEL_PATH = os.environ.get("GAME_MODEL_PATH")
if not GPU or not GPU.isdigit() or not MODEL_PATH:
    raise RuntimeError("Set GAME_MODEL_GPU (one physical index) and GAME_MODEL_PATH (local model directory)")
os.environ.update(CUDA_VISIBLE_DEVICES=GPU, HF_HUB_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
import json, time, signal, subprocess, uuid
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
ROOT = Path(__file__).resolve().parent
MODEL = {"name":"Qwen/Qwen2.5-Coder-7B-Instruct", "revision":os.environ.get("GAME_MODEL_REVISION", "local-unverified"), "source":"https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct", "license":"Apache-2.0", "backend":"transformers", "device":f"CUDA physical GPU {GPU}", "role":"public alternative, not paper AWoMo/Cosmos"}
PORT = int(os.environ.get("GAME_MODEL_PORT", "18745"))
CALL_LIMIT = int(os.environ.get("GAME_MODEL_CALL_LIMIT", "5"))
if CALL_LIMIT < 1 or not 1 <= PORT <= 65535:
    raise ValueError("Invalid call limit or port")
if not Path(MODEL_PATH).is_dir():
    raise ValueError("GAME_MODEL_PATH must be an existing local model directory")
STATE = ROOT / "inference_count.json"
AUDIT = ROOT / "requests"
AUDIT.mkdir(exist_ok=True)
used = int(subprocess.check_output(["nvidia-smi",f"--id={GPU}","--query-gpu=memory.used","--format=csv,noheader,nounits"],text=True).strip())
if used > 100: raise RuntimeError(f"GPU {GPU} occupied ({used} MiB); refusing load")
import torch, transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
torch.set_num_threads(4)
MODEL.update(torch_version=torch.__version__,transformers_version=transformers.__version__)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True, trust_remote_code=False)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0").eval()
def count():
    return json.loads(STATE.read_text()).get("count",0) if STATE.exists() else 0
def timeout_handler(*_): raise TimeoutError("Inference exceeded 180 seconds")
signal.signal(signal.SIGALRM, timeout_handler)
class Handler(BaseHTTPRequestHandler):
    def send(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path!="/health":return self.send(404,{"error":"not found"})
        self.send(200,{"status":"ready","model":MODEL,"calls_used":count(),"calls_limit":CALL_LIMIT})
    def do_POST(self):
        if self.path!="/generate":return self.send(404,{"error":"not found"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0 < length <= 131072:raise ValueError("Request body must be 1..131072 bytes")
            request=json.loads(self.rfile.read(length))
            rid=str(request.get("request_id") or uuid.uuid4())
            if not rid or len(rid)>100 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in rid):raise ValueError("Invalid request_id")
            record=AUDIT/rid
            if (record/"response.json").exists():return self.send(200,json.loads((record/"response.json").read_text()))
            if (record/"request.json").exists():return self.send(409,{"error":"This request was attempted but has no successful response; inspect audit before retrying"})
            messages=request.get("messages")
            if not isinstance(messages,list) or not messages or any(not isinstance(m,dict) or m.get("role") not in {"system","user","assistant"} or not isinstance(m.get("content"),str) for m in messages):raise ValueError("Invalid messages")
            limit=int(request.get("max_new_tokens",4096));temperature=float(request.get("temperature",0))
            if not 1<=limit<=4096 or not 0<=temperature<=1:raise ValueError("Invalid token limit or temperature")
            if count()>=CALL_LIMIT:return self.send(429,{"error":"Configured inference budget exhausted"})
            text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            batch=tokenizer(text,return_tensors="pt").to("cuda:0")
            if batch.input_ids.shape[1]>12000:raise ValueError("Input exceeds 12000 tokens")
            record.mkdir(exist_ok=True);(record/"request.json").write_text(json.dumps(request,ensure_ascii=False,indent=2));STATE.write_text(json.dumps({"count":count()+1}))
            started=time.time();signal.alarm(180)
            try:
                torch.manual_seed(0)
                kwargs={"max_new_tokens":limit,"do_sample":temperature>0,"pad_token_id":tokenizer.eos_token_id}
                if temperature>0:kwargs["temperature"]=temperature
                with torch.inference_mode():output=model.generate(**batch,**kwargs)
                generated=output[0,batch.input_ids.shape[1]:]
                response={"request_id":rid,"raw_text":tokenizer.decode(generated,skip_special_tokens=True),"model":MODEL,"usage":{"input_tokens":batch.input_ids.shape[1],"output_tokens":len(generated)},"elapsed_seconds":time.time()-started,"finish_reason":"length" if len(generated)>=limit else "stop","calls_used":count(),"calls_limit":CALL_LIMIT}
                (record/"response.json").write_text(json.dumps(response,ensure_ascii=False,indent=2));self.send(200,response)
            except Exception as exc:
                (record/"error.json").write_text(json.dumps({"error":str(exc)}));raise
            finally:signal.alarm(0)
        except ValueError as exc:self.send(400,{"error":str(exc)})
        except Exception as exc:self.send(500,{"error":str(exc)})
    def log_message(self,fmt,*args):print(fmt%args,flush=True)
print(json.dumps({"status":"ready","port":PORT,"model":MODEL}),flush=True)
HTTPServer(("127.0.0.1",PORT),Handler).serve_forever()

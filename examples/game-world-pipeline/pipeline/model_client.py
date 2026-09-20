"""Bounded SSH client for the isolated DSW public-model alternative.

No model output is executed. Caller persists request, raw response and parsed scene.
"""
import argparse
import json
import os
import subprocess
import uuid
from pathlib import Path

class ModelClient:
    def __init__(self, host=None, remote_root=None, timeout=210):
        self.host = host or os.environ.get("GAME_MODEL_SSH_HOST")
        self.remote_root = remote_root or os.environ.get("GAME_MODEL_REMOTE_ROOT")
        self.timeout = timeout
        self.port = int(os.environ.get("GAME_MODEL_PORT", "18745"))
        if not self.host or not self.remote_root:
            raise ValueError("Set GAME_MODEL_SSH_HOST and GAME_MODEL_REMOTE_ROOT; see deploy/README.md")
        if self.host.startswith("-") or not self.remote_root.startswith("/"):
            raise ValueError("SSH host must not start with '-' and remote root must be absolute")
        if not 1 <= self.port <= 65535:
            raise ValueError("GAME_MODEL_PORT must be in 1..65535")

    def _call(self, mode, payload=None):
        # Remote command arguments are fixed configuration, never model text.
        import shlex
        command = " ".join(shlex.quote(x) for x in ["python3",self.remote_root+"/rpc_client.py",mode,str(self.port)])
        proc = subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8",self.host,command],
                              input=json.dumps(payload,ensure_ascii=False) if payload is not None else "",
                              text=True,capture_output=True,timeout=self.timeout)
        try: result=json.loads(proc.stdout)
        except json.JSONDecodeError as exc: raise RuntimeError(f"Model transport error (exit {proc.returncode}): {proc.stderr[-1000:]}") from exc
        if proc.returncode or "error" in result: raise RuntimeError(result.get("error",proc.stderr[-1000:]))
        return result

    def health(self):
        return self._call("health")

    def generate(self,messages,max_new_tokens=4096,temperature=0,request_id=None):
        if not 1<=max_new_tokens<=4096:raise ValueError("max_new_tokens must be in 1..4096")
        return self._call("generate",{"messages":messages,"max_new_tokens":max_new_tokens,
                         "temperature":temperature,"request_id":request_id or str(uuid.uuid4())})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health",action="store_true")
    parser.add_argument("--request",type=Path,help="JSON with messages, optional max_new_tokens/temperature/request_id")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    client=ModelClient()
    if args.health:result=client.health()
    elif args.request:result=client.generate(**json.loads(args.request.read_text()))
    else:parser.error("Use --health or --request")
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:args.output.write_text(text+"\n")
    else:print(text)

if __name__=="__main__":main()

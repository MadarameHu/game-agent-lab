import json,sys,urllib.request,urllib.error
port=int(sys.argv[2]) if len(sys.argv)>2 else 18745
if not 1<=port<=65535:raise SystemExit("invalid port")
mode=sys.argv[1] if len(sys.argv)>1 else "generate"
if mode not in {"generate","health"}:raise SystemExit("invalid mode")
req=urllib.request.Request(f"http://127.0.0.1:{port}/"+mode,data=sys.stdin.buffer.read() if mode=="generate" else None,headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req,timeout=195) as response:sys.stdout.buffer.write(response.read())
except urllib.error.HTTPError as exc:
    sys.stdout.buffer.write(exc.read());sys.exit(2)

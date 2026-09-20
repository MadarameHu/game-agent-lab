# 历史模型与当前调用边界

本实现使用公开的 **Qwen/Qwen2.5-Coder-7B-Instruct**，并非论文的 AWoMo、UnifiedGameAssetModel 或 Cosmos。模型输出场景 JSON 文本；Godot 独立检查场景，模型不计算验证标签，也没有执行其输出的能力。本次只做推理与数据记录，没有模型训练更新。

- 权重来源：https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- 固定 revision：`c03e6d358207e414f1eca0bb1891e29f1db0e242`
- 许可证：Apache-2.0；https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/blob/main/LICENSE
- 复用远端既有完整缓存，四个 safetensors 分片共 **15,231,271,864 字节**，本次未下载模型权重。
- 原运行复用了独立 DSW 服务。公开版不包含私有主机或目录配置；新部署使用 `GAME_MODEL_SSH_HOST` 和 `GAME_MODEL_REMOTE_ROOT`。
- 当前部署须显式设置 `GAME_MODEL_GPU`，映射为进程内 `cuda:0`；启动前若该卡已用显存超过 100 MiB 则拒绝加载。
- 后端：PyTorch `2.10.0+cu128`、Transformers `4.57.6`，BF16、SDPA。任务 `.venv` 复用全局 PyTorch，但 Transformers/HF Hub/Numpy 在任务 venv 中覆盖，不修改全局环境。

## 调用

本地标准库客户端通过 SSH 将 JSON 写到远端固定 `rpc_client.py` 的 stdin，再访问仅监听 `127.0.0.1:18745` 的服务。不开放公网端口、不创建本地常驻 tunnel、不使用 API Key。

```python
from pipeline.model_client import ModelClient

client = ModelClient()  # 需先配置环境变量，见 deploy/README.md
health = client.health()  # 无模型推理，不计预算
response = client.generate(
    messages=[
        {"role": "system", "content": "Return only valid scene JSON. Never produce executable code."},
        {"role": "user", "content": "...任务、完整场景与实际 Godot 诊断..."},
    ],
    max_new_tokens=4096,
    temperature=0,
    request_id="run-id-candidate-1",
)
raw_text = response["raw_text"]
```

CLI：`python3 pipeline/model_client.py --health`；或 `--request request.json --output response.json`。request JSON 包含 `messages`，可选 `request_id`、`max_new_tokens`、`temperature`。响应保留 `raw_text`、实际 `model` 元数据、输入输出 token 数、耗时和 `finish_reason`，调用方负责将完整请求与响应写入本地轨迹。

模型请求必须固定 room/player/goal、保留对象稳定 ID 和至少六个对象，仅修改场景 JSON 允许的属性。解析和验证由调用方与引擎完成；本客户端不把模型文本写进 shell 命令。

## 限额与失败记录

服务单 worker，默认最多 **5 次实际推理**，由新部署的 `GAME_MODEL_CALL_LIMIT` 配置。计数在远端 `inference_count.json` 持久化；推理失败仍计一次。请求正文最大 128 KiB、输入最多 12,000 tokens、输出最多 4,096 tokens；推理180秒超时、SSH客户端210秒超时，不自动重试。默认 greedy decoding；允许 `temperature=0.1` 等显式采样。

每个请求在远端 `requests/<request_id>/` 保存 `request.json` 和 `response.json` 或 `error.json`。已有成功 response 的同一个 request ID 幂等返回，不重复推理。已有 request 但无成功 response 时拒绝自动重试，以免在客户端超时后重复消耗资源。request ID 仅允许字母、数字、短横线、下划线，不能逃逸工作目录。

`finish_reason="length"` 表示达到输出上限，不能把截断文本当成有效场景。生成结果始终是未验证候选，必须经过 Godot 检查，最终仍需人类在本地审阅页面明确接受。

## 远端进程

服务源码 `server.py`、转发器 `rpc_client.py`、`server.log` 和 `server.pid` 均在任务远端目录。服务不会自动重启，也不会因推理预算用完而清除审计数据。停止服务时先核对 `server.pid` 对应命令确为这个目录的 `server.py`，再只停止该进程；不要使用 `pkill python` 或 GPU 级清理命令。

本地缓存的 Godot 场景、截图、诊断和训练格式导出不依赖远端持续在线；重新推理需要 SSH 连通且远端服务仍在运行。

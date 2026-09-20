# 自行部署历史示例的模型服务

这个可选服务用于新增仓库布局/修复数据。查看已有两次历史运行不需要部署。公开版将原运行的固定 SSH 主机、目录和 GPU 改成显式配置；没有调用模型、下载权重或重启原服务。`runs/` 保留原始请求、响应与模型元数据。

## 运行条件

在自己的 Linux NVIDIA GPU 主机上部署；进程管理使用 Linux `/proc`。历史环境为 Python 3.12、PyTorch 2.10.0+cu128、Transformers 4.57.6，BF16/SDPA。请先安装与自己 CUDA 环境匹配的 PyTorch，并准备完整 Qwen2.5-Coder-7B-Instruct 本地权重目录。该示例约15.2 GB权重，推理还需要额外显存；启动前自行确认容量和空闲情况。

历史权重 revision 为 `c03e6d358207e414f1eca0bb1891e29f1db0e242`，来源 https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct ，Apache-2.0。服务使用 `local_files_only=True`、`HF_HUB_OFFLINE=1`、`trust_remote_code=False`，不会自动下载权重。当前服务支持该 Qwen 模型，不承诺任意权重可替换。

## 远端准备

把本目录的 `server.py`、`rpc_client.py`、`manage.py`、`start.sh`、`stop.sh`、`requirements.txt` 复制到自己选择的同一个远端目录。进入该目录执行：

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt

# 以下值均换成自己的实际配置；环境变量应在每次管理服务的 shell 中设置。
export GAME_MODEL_GPU="0"
export GAME_MODEL_PATH="/absolute/path/to/Qwen2.5-Coder-7B-Instruct"
export GAME_MODEL_REVISION="c03e6d358207e414f1eca0bb1891e29f1db0e242"
export GAME_MODEL_CALL_LIMIT="5"
export GAME_MODEL_PORT="18745"
python3 manage.py start
python3 manage.py status
```

`GAME_MODEL_GPU` 必须是单个物理 GPU 编号，`GAME_MODEL_PATH` 必须是完整本地模型目录，二者没有默认值。`GAME_MODEL_REVISION` 是部署者声明的权重版本；未设置时响应记录 `local-unverified`，服务不会自动认证本地权重。调用上限默认5次、端口默认18745。启动前管理器和模型进程均检查所选 GPU 的已用显存，超过100 MiB则拒绝加载。服务仅监听远端 `127.0.0.1`，单worker。

## 本地连接

在本地示例根目录设置自己的 SSH 目标与上述远端目录：

```bash
export GAME_MODEL_SSH_HOST="your-ssh-host"
export GAME_MODEL_REMOTE_ROOT="/absolute/path/to/remote/service"
export GAME_MODEL_PORT="18745"
python3 pipeline/model_client.py --health
```

本机使用既有 SSH 密钥/配置认证，仓库不包含凭证。客户端通过 SSH 调用远端 `python3 rpc_client.py`，向仅监听 loopback 的服务转发 JSON；不需要公网 HTTP 或 API Key。本地端口配置必须与远端一致。健康检查不执行推理。

## 管理与预算

在远端服务目录使用 `python3 manage.py stop` / `restart` / `status`。端口配置须与启动时一致。管理器只核对本目录 `server.pid`，并验证 `/proc/PID/cmdline` 精确等于本目录venv、`-u`、本目录 `server.py` 才发送 SIGTERM；不会杀其他进程。停止前先让当前推理结束。启动最多等待120秒，失败查看本目录 `server.log`。

计数保存在 `inference_count.json`，请求和结果在 `requests/<request_id>/`。失败也计数，start/stop/restart不重置预算。为新实验设置明确预算；不要删除审计状态来隐式绕过限额。成功 request ID 可幂等重取，失败或超时且已记录的 ID 不自动重试。输出最多4096 tokens、输入最多12000 tokens、生成180秒超时。

模型只输出文本，调用方解析场景动作并交 Godot 验证。这里没有 RL 训练，也没有模型给自己判定通过。

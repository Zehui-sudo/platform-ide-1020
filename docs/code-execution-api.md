# 代码执行 API（最小可用版本）

本地 FastAPI 服务现已提供一个用于执行临时代码片段的实验性端点，作为未来 Docker 沙箱方案的占位实现。

## 端点

- `POST /api/execute/run`
  - `language`：目前仅支持 `python`
  - `code`：待执行的 Python 源码（字符串）
  - `timeout`（可选）：最长执行时间，秒。默认 10s，上限 30s

### 响应示例

```json
{
  "status": "success",
  "language": "python",
  "stdout": "hello\\n",
  "stderr": "",
  "exitCode": 0,
  "timedOut": false,
  "duration": 0.124
}
```

- `status`：`success` | `timeout` | `error`
- `stdout` / `stderr`：标准输出、标准错误（截断到 10KB）
- `exitCode`：子进程退出码；沙箱或服务器错误时为 `null`
- `timedOut`：是否发生超时
- `duration`：执行耗时（秒）

## 测试方式

```bash
curl -X POST http://127.0.0.1:8000/api/execute/run \
  -H 'Content-Type: application/json' \
  -d '{
        "language": "python",
        "code": "import time\nprint(\"hello\")\ntime.sleep(0.5)"
      }'
```

## 当前限制

- 每次请求都会启动一次 Docker 容器，未来可引入容器池以降低冷启动成本。
- 仍未开放外网访问与自定义依赖安装，如需复杂库需预先打包入镜像。
- 资源限制（CPU/内存/时限）为基础配置，生产环境需结合监控与更细粒度的配额。

## 下一步

1.（可选）引入容器池或任务队列，降低频繁 `docker run` 带来的开销。
2. 扩展镜像或增加多语言镜像，支持更多运行时。
3. 加入日志采集、安全审计、网络隔离策略，并补齐自动化部署流程。

## 沙箱镜像（设计草案）

仓库内新增了 `docker/sandbox/Dockerfile` 与 `runner.py`，用于构建一个最小 Python 执行环境。构建方式：

```bash
docker build \
  -f docker/sandbox/Dockerfile \
  -t platform-ide-python-sandbox \
  docker/sandbox
```

镜像入口脚本会从标准输入读取 JSON（包含 `code`、可选 `timeout`），执行后输出结构化结果。FastAPI 通过 `docker run --rm -i platform-ide-python-sandbox` 管道调用容器，再把 JSON 映射到 `/api/execute/run` 响应；前端 `InteractiveCodeBlock` 已直接调用该端点。

部署时可通过环境变量 `SANDBOX_IMAGE` 指定镜像名称（默认 `platform-ide-python-sandbox`），以便在不同环境使用同一套 API。

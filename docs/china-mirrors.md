# 中国镜像源配置

本项目默认使用 Anaconda 管理本地开发环境，并优先使用国内镜像源下载依赖。

## Conda 和 pip

推荐先执行：

```powershell
.\scripts\config_conda_mirrors.ps1
```

该脚本会配置：

- Conda：清华 Anaconda 镜像源。
- pip：清华 PyPI 镜像源。

创建或更新项目环境：

```powershell
.\scripts\create_conda_env.ps1
```

激活环境：

```powershell
conda activate E:\Emotion\.conda\emotion
```

## Docker

Dockerfile 内部的 pip 安装已经使用清华 PyPI 镜像。

Dockerfile 的基础镜像默认使用 `docker.1ms.run` 镜像代理，后端 Dockerfile 的 Debian apt 源已经替换为清华镜像。前端 Dockerfile 的 npm registry 已经替换为 npmmirror。

本地安装前端依赖请使用 Conda 环境里的 npm：

```powershell
.\scripts\install_frontend.ps1
```

Docker 基础镜像拉取速度取决于 Docker Desktop 的 registry mirror 配置。可以在 Docker Desktop 的 Settings -> Docker Engine 中加入可用的国内镜像加速地址，例如：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run"
  ]
}
```

保存并重启 Docker Desktop 后再执行：

```powershell
docker compose up --build
```

镜像加速地址可用性会变化，如果拉取失败，需要替换成当前可用的 Docker 镜像加速服务。

也可以在构建时覆盖基础镜像：

```powershell
docker compose build --build-arg PYTHON_IMAGE=python:3.11-slim --build-arg NODE_IMAGE=node:22-alpine
```

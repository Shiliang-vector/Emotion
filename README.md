# 人脸识别心情判别系统

本项目是一个基于交流视频的心情判别本地原型系统。系统以视频为输入，结合人脸表情、语音转写、声学特征和大语言模型专家意见，输出整段视频的情绪预判结果。

## 第一版目标

- 上传一段交流视频并创建分析任务。
- 从视频中提取关键帧和音频。
- 使用 DeepFace 服务负责人脸识别和表情分析。
- 使用 SenseVoice 服务负责语音转写和语音侧信息提取。
- 汇总表情时长概率、语音语义和声学特征。
- 使用 OpenAI 兼容协议调用大语言模型生成专家意见。
- 通过前端页面展示上传、任务状态和最终报告。

## 项目结构

```text
.
├── backend/                 # FastAPI 后端
├── frontend/                # React + Vite 前端
├── model-services/          # Docker 化模型服务
│   ├── deepface/            # 人脸和表情分析服务
│   └── sensevoice/          # 语音转写和语音侧分析服务
├── docs/                    # 架构、API、情绪融合规则
├── scripts/                 # 本地开发脚本
├── storage/                 # 上传文件、抽帧、音频、报告
├── docker-compose.yml
└── .env.example
```

## 快速启动

1. 配置国内镜像源：

```powershell
.\scripts\config_conda_mirrors.ps1
```

2. 创建 Anaconda 项目环境：

```powershell
.\scripts\create_conda_env.ps1
```

3. 安装并构建前端依赖：

```powershell
.\scripts\install_frontend.ps1
```

4. 复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

5. 根据实际模型服务和大语言模型配置编辑 `.env`。

6. 启动全部服务：

```powershell
docker compose up --build
```

7. 打开：

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/docs
- DeepFace 服务：http://localhost:8001/health
- SenseVoice 服务：http://localhost:8002/health

## 当前实现说明

第一版代码先搭建端到端框架。`model-services/deepface` 已接入真实 DeepFace，用于分析抽帧后的人脸表情概率和持续时长比例。`model-services/sensevoice` 仍是可运行的占位服务，接口稳定，便于后续替换为真实 SenseVoice 推理逻辑。

首次运行 DeepFace 分析时，容器可能需要下载 DeepFace 情绪模型权重，速度取决于网络。Docker Compose 已配置 `deepface-cache` 卷缓存模型文件，后续运行会复用缓存。

LLM 专家意见使用 OpenAI 兼容接口。若未配置 `OPENAI_API_KEY`，系统会返回本地兜底建议，保证原型流程可以完整跑通。

## 环境管理

本地开发统一使用 Anaconda，环境文件为 `environment.yml`，默认环境路径为 `.conda\emotion`。国内镜像源配置见 `docs/china-mirrors.md`。

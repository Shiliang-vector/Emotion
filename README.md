# 多模态心理咨询辅助系统

本项目是一个基于交流视频的多模态心理咨询辅助原型系统。系统以视频为输入，结合人脸表情、语音转写、声学特征和大语言模型专家意见，为普通用户输出非诊断性建议，并为心理咨询师提供历史查看和辅助工作草稿。

## 当前目标

- 普通用户登录后上传交流视频并创建分析任务。
- 从视频中提取关键帧和音频。
- 使用 DeepFace 服务负责人脸识别和表情分析。
- 使用 SenseVoice 服务负责语音转写和语音侧信息提取。
- 汇总表情时长概率、语音语义和声学特征。
- 使用 OpenAI 兼容协议调用大语言模型生成普通用户侧专家建议。
- 心理咨询师查看已关联普通用户的分析历史，并生成供专业人员参考的辅助建议草稿。
- 前端提供工作台、心理科普和项目说明三个站内视图，便于课程答辩展示。
- 所有自动输出均为辅助、非诊断性内容，不能替代专业诊断或治疗。

## 项目结构

```text
.
├── backend/                 # FastAPI 后端
├── frontend/                # React + Vite 前端
├── model-services/          # Docker 化模型服务
│   ├── deepface/            # 人脸和表情分析服务
│   └── sensevoice/          # 语音转写和语音侧分析服务
├── docs/                    # 架构、API、情绪融合规则、小论文和PPT资料
├── scripts/                 # 本地开发脚本
├── storage/                 # 上传文件、抽帧、音频、报告
├── docker-compose.yml
└── .env.example
```

## 快速启动：本地 Conda 开发

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

首次启动后会自动创建两个演示账号：

- 普通用户：`client@example.com` / `client123`
- 心理咨询师：`counselor@example.com` / `counselor123`

前端已经使用标准 Vite React 脚本。若手动运行前端命令，请先激活 Conda 环境：

```powershell
conda activate E:\Emotion\.conda\emotion
cd frontend
npm run build
npm run dev
```

## 快速启动：已有 Docker 镜像

如果本机已经构建过 `emotion-frontend`、`emotion-backend`、`emotion-deepface`、`emotion-sensevoice` 镜像，可以不重新构建，直接启动：

```powershell
docker compose up -d --no-build
```

查看状态：

```powershell
docker compose ps
```

## 当前实现说明

当前代码已经搭建端到端框架，并使用 `fastapi-users` 提供注册、JWT 登录和当前用户能力。数据库默认使用 PostgreSQL，表结构由 Alembic 管理。`model-services/deepface` 已接入真实 DeepFace，用于分析抽帧后的人脸表情概率和持续时长比例。`model-services/sensevoice` 已接入 FunASR SenseVoiceSmall，用于语音转写、语音侧情绪标签解析和基础声学特征估计。

首次运行 DeepFace 分析时，容器可能需要下载 DeepFace 情绪模型权重，速度取决于网络。Docker Compose 已配置 `deepface-cache` 卷缓存模型文件，后续运行会复用缓存。

首次运行 SenseVoice 分析时，容器可能需要从 ModelScope 下载 `iic/SenseVoiceSmall` 和 VAD 模型。Docker Compose 已配置 `sensevoice-cache` 卷缓存模型文件，后续运行会复用缓存。

LLM 专家意见使用 OpenAI 兼容接口。若未配置 `OPENAI_API_KEY`，系统会返回本地兜底建议，保证原型流程可以完整跑通。

## 界面与科普模块

前端已经从单纯工具页面升级为课程展示型界面：

- 顶部导航包含“工作台、心理科普、项目说明”。
- 首页和科普页使用本地静态配图，位于 `frontend/public/images/`，Docker 和离线答辩均可加载。
- 普通用户工作台展示上传入口、任务状态、历史记录、授权咨询师和报告详情。
- 心理咨询师工作台展示绑定用户、用户历史、辅助建议、人工备注和趋势摘要。
- 心理科普页覆盖抑郁、焦虑、睡眠、压力适应、创伤后应激和强迫相关问题，并明确非诊断性边界。
- 报告页展示模型名、prompt 版本、生成时间、风险依据和非诊断性声明，方便答辩说明系统可追溯。

## 小论文和 PPT 资料入口

交付给组员写小论文或制作 PPT 时，建议从以下文档开始：

- `docs/paper-guide.md`：小论文写作指南，包含摘要、背景、系统设计、技术路线、测试、伦理边界、局限性和未来工作。
- `docs/ppt-outline.md`：PPT 页面大纲、每页讲解重点和截图建议。
- `docs/demo-checklist.md`：答辩前演示验收清单、启动命令、演示账号、截图清单和常见问题。
- `docs/architecture.md`：系统架构、服务职责、数据流和权限边界。
- `docs/api.md`：认证、上传、报告、咨询师和导出接口说明。

## 课程演示流程

1. 执行 `docker compose up --build`，等待 `postgres` 显示 healthy，后端日志出现 `Application startup complete`。
2. 打开前端，使用 `client@example.com / client123` 登录普通用户。
3. 切换“心理科普”和“项目说明”，展示系统的用户教育能力、伦理边界和项目架构。
4. 回到“工作台”，查看“已授权咨询师”，上传一段交流视频，等待任务状态从抽帧、表情分析、语音分析到报告完成。
5. 在普通用户历史中打开报告，展示主情绪、风险等级、人脸表情、语音特征、风险依据和非诊断性专家意见。
6. 导出 JSON 或文本报告，用于说明系统可追溯和可复核。
7. 退出后使用 `counselor@example.com / counselor123` 登录心理咨询师。
8. 在“关联用户”中查看普通用户历史，生成咨询师辅助建议，添加人工备注，展示趋势摘要。

## 非诊断性声明

本系统是课程设计中的心理咨询辅助工具，只能作为沟通线索和辅助参考。系统不会也不应替代心理咨询师、精神科医生或其他专业人员的诊断、治疗和危机干预判断。报告中的风险等级、情绪标签和建议必须结合真实访谈背景复核。

## 环境管理

本地开发统一使用 Anaconda，环境文件为 `environment.yml`，默认环境路径为 `.conda\emotion`。前端依赖使用 `package-lock.json` 锁定，Docker 前端构建使用 `npm ci`。国内镜像源配置见 `docs/china-mirrors.md`。

数据库默认使用 `postgresql+asyncpg://emotion:emotion@postgres:5432/emotion`。Docker Compose 会启动 `postgres` 服务，后端容器启动时会执行 `alembic upgrade head` 初始化或升级表结构。

运行时文件保存在 `storage/`：上传视频、抽帧、音频和报告 JSON 会随本地目录保留。课程演示阶段不自动删除这些文件；后续若进入真实使用，需要增加用户数据删除和文件保留周期策略。

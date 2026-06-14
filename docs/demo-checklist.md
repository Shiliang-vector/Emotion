# 演示验收清单

本清单用于答辩前自检，也可交给组员录制演示视频或制作 PPT 截图。

## 启动前检查

- 已复制 `.env.example` 为 `.env`。
- `.env` 中没有准备提交的真实 API Key。
- Docker Desktop 已启动。
- 当前目录为项目根目录 `E:\Emotion`。

## 启动命令

```powershell
docker compose up -d --build
```

如果镜像已经构建过：

```powershell
docker compose up -d --no-build
```

## 服务状态

```powershell
docker compose ps
```

预期服务：

- `postgres`：healthy
- `backend`：Up
- `frontend`：Up
- `deepface`：Up
- `sensevoice`：Up

健康检查：

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

预期返回：

```json
{"status":"ok"}
```

## 一键自检

服务启动后可运行：

```powershell
.\scripts\check_demo.ps1
```

该脚本会检查 Docker 服务、后端健康接口、前端访问和演示账号登录。

## 生成演示样例数据

如果不想完全依赖现场上传视频，可以运行：

```powershell
.\scripts\seed_demo_data.ps1
```

该脚本会生成三条模拟历史报告、一条咨询师辅助建议和一条咨询备注。样例数据只用于课程展示，不包含真实隐私视频。

## 演示账号

- 普通用户：`client@example.com` / `client123`
- 心理咨询师：`counselor@example.com` / `counselor123`

## 演示流程

1. 打开前端：http://localhost:5173
2. 展示首页主视觉和顶部导航。
3. 切换到“心理科普”，展示常见心理问题和非诊断性声明。
4. 切换到“项目说明”，说明架构和课程设计定位。
5. 回到“工作台”，使用普通用户登录。
6. 上传演示视频，观察任务状态：视频处理、人脸分析、语音分析、多模态融合、专家意见。
7. 打开报告，展示主情绪、风险等级、证据、模型名、prompt 版本和非诊断性声明；需要截图时可打开“截图模式”。
8. 导出 JSON 或文本报告。
9. 退出登录，使用心理咨询师账号登录。
10. 查看绑定用户列表。
11. 打开用户历史，生成咨询师辅助建议。
12. 添加人工备注，展示趋势摘要。

## 截图建议

- 首页主视觉。
- 心理科普页。
- 普通用户上传区。
- 任务状态进度条。
- 报告详情页。
- 报告截图模式。
- 咨询师关联用户页。
- 辅助建议、趋势图和备注区域。
- Docker 服务状态。

## 常见问题

- 前端打不开：检查 `frontend` 服务是否 Up，端口是否为 `5173`。
- 后端健康检查失败：检查 `backend` 日志和 PostgreSQL 是否 healthy。
- 登录失败：确认演示账号已由后端启动时自动种子创建。
- 视频分析长时间未完成：首次 DeepFace 或 SenseVoice 可能下载模型，等待后再次查看日志。
- 报告为空：确认任务状态已完成，失败任务会显示错误原因。
- 图片不显示：确认 `frontend/public/images/hero-counseling.png` 和 `education-mental-health.png` 存在。

## 伦理边界提示

答辩时应主动说明：

- 系统是心理咨询辅助项目，不是诊断系统。
- 科普页面不能用于自我诊断。
- 风险等级只是复核提示。
- 紧急情况应联系专业机构或当地紧急服务。

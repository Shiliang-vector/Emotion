# 课程答辩演示脚本

## 5-8 分钟演示路线

1. 展示架构图：React 前端、FastAPI 后端、PostgreSQL、DeepFace、SenseVoice、LLM。
2. 打开 Docker 状态：确认 `postgres`、`backend`、`frontend`、`deepface`、`sensevoice` 全部运行。
3. 普通用户登录：`client@example.com / client123`。
4. 上传视频并说明处理阶段：抽帧、语音提取、人脸分析、语音分析、多模态融合、专家意见。
5. 打开报告：说明主情绪、置信度、风险等级、人脸表情概率、语音转写和专家意见。
6. 导出报告：展示 JSON 或文本导出，说明可复核。
7. 咨询师登录：`counselor@example.com / counselor123`。
8. 查看用户历史，生成咨询师辅助建议，添加人工备注，展示趋势摘要。
9. 结束时强调：系统是心理咨询辅助工具，不能替代诊断或治疗。

## 答辩重点

- 使用 `fastapi-users` 减少账号模块开发量。
- 使用 PostgreSQL 和 Alembic，让数据库结构更规范。
- 通过绑定关系控制咨询师访问权限。
- 多模态结果由人脸、语音、文本语义和 LLM 建议组合生成。
- 所有建议都带有非诊断性边界。

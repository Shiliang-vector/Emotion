# 架构说明

系统采用前后端分离和模型服务解耦架构。

## 服务职责

- `frontend`：视频上传、任务状态轮询、报告展示。
- `backend`：任务编排、视频处理、特征融合、报告持久化、LLM 调用。
- `deepface`：人脸检测、身份识别、表情概率和持续时长分析。
- `sensevoice`：语音转写、语义情绪和语音侧信息分析。

## 数据流

1. 前端调用 `POST /api/videos/upload` 上传交流视频。
2. 后端保存视频到 `storage/uploads`，创建任务 ID。
3. 后端从视频中抽取关键帧到 `storage/frames/{task_id}`。
4. 后端从视频中提取音频到 `storage/audio/{task_id}.wav`。
5. 后端调用 DeepFace 服务分析帧级表情。
6. 后端调用 SenseVoice 服务分析音频。
7. 后端融合视觉、语音和声学信息。
8. 后端调用 OpenAI 兼容接口生成专家意见。
9. 后端保存报告到 `storage/reports/{task_id}.json`。

## 替换真实模型

当前模型服务为占位实现。后续替换时保持 HTTP 接口不变即可：

- DeepFace：`POST /analyze`
- SenseVoice：`POST /analyze`


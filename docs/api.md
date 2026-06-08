# API 说明

## 健康检查

```http
GET /api/health
```

返回：

```json
{
  "status": "ok"
}
```

## 上传视频

```http
POST /api/videos/upload
Content-Type: multipart/form-data
```

字段：

- `file`：视频文件。

返回：

```json
{
  "task_id": "uuid",
  "status": "queued",
  "stage": "queued",
  "progress": 5,
  "message": "视频已上传，等待后台分析",
  "error": null,
  "created_at": "2026-06-08T21:30:00",
  "updated_at": "2026-06-08T21:30:00",
  "report_url": null
}
```

## 查询任务

```http
GET /api/tasks/{task_id}
```

返回：

```json
{
  "task_id": "uuid",
  "status": "completed",
  "stage": "completed",
  "progress": 100,
  "message": "分析完成",
  "error": null,
  "created_at": "2026-06-08T21:30:00",
  "updated_at": "2026-06-08T21:32:00",
  "report_url": "/api/reports/uuid"
}
```

`stage` 可能值：

- `queued`
- `preparing_video`
- `analyzing_face`
- `analyzing_speech`
- `fusing_features`
- `generating_advice`
- `saving_report`
- `completed`
- 失败时 `status` 为 `failed`，`stage` 保留失败发生前的处理阶段。

## 查询报告

```http
GET /api/reports/{task_id}
```

返回完整情绪分析报告。

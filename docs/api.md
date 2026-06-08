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
  "status": "completed"
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
  "report_url": "/api/reports/uuid"
}
```

## 查询报告

```http
GET /api/reports/{task_id}
```

返回完整情绪分析报告。


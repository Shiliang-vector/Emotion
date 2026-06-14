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

## 认证

```http
POST /api/auth/register
Content-Type: application/json
```

请求：

```json
{
  "email": "client_a@example.com",
  "password": "client123",
  "role": "client",
  "display_name": "普通用户A"
}
```

`role` 只能是 `client` 或 `counselor`。

```http
POST /api/auth/jwt/login
Content-Type: application/x-www-form-urlencoded
```

请求：

```text
username=client@example.com&password=client123
```

返回：

```json
{
  "access_token": "jwt",
  "token_type": "bearer"
}
```

```http
GET /api/users/me
Authorization: Bearer <token>
```

返回当前用户信息，包含 `email`、`role`、`display_name` 等字段。

## 上传视频

```http
POST /api/videos/upload
Authorization: Bearer <client token>
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
  "report_url": null,
  "user_id": 1
}
```

## 查询任务

```http
GET /api/tasks/{task_id}
Authorization: Bearer <token>
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
  "report_url": "/api/reports/uuid",
  "user_id": 1
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
Authorization: Bearer <token>
```

返回完整情绪分析报告。

## 普通用户历史

```http
GET /api/me/tasks
Authorization: Bearer <client token>
```

返回当前普通用户自己的分析任务列表。每条任务包含状态、创建时间、报告入口，以及已完成报告的主情绪、风险等级和置信度摘要。

```http
GET /api/me/counselors
Authorization: Bearer <client token>
```

返回当前普通用户已授权的心理咨询师列表。

```http
DELETE /api/me/tasks/{task_id}
Authorization: Bearer <client token>
```

删除当前普通用户自己的已完成或失败任务。删除时同步清理数据库报告记录和本地运行文件。处理中任务返回 `409`，其他用户任务返回 `404`。

## 咨询师接口

```http
GET /api/counselor/clients
Authorization: Bearer <counselor token>
```

返回当前咨询师已关联的普通用户列表，包含分析次数和最近一次报告摘要。

```http
POST /api/counselor/bindings
Authorization: Bearer <counselor token>
Content-Type: application/json
```

请求：

```json
{
  "client_email": "client@example.com"
}
```

绑定普通用户。只有绑定后，咨询师才能查看该用户历史、报告、趋势和备注。

```http
DELETE /api/counselor/bindings/{client_id}
Authorization: Bearer <counselor token>
```

解除绑定。

```http
GET /api/counselor/users/{user_id}/history
Authorization: Bearer <counselor token>
```

返回该普通用户的分析历史。只能访问已关联用户。

```http
POST /api/counselor/users/{user_id}/assistance-draft
Authorization: Bearer <counselor token>
```

基于该用户最近的分析历史生成咨询师辅助建议草稿。该内容仅供专业人员参考，不能替代诊断或治疗。

返回：

```json
{
  "user_id": 1,
  "assistance": "仅供专业人员参考...",
  "generated_at": "2026-06-14T10:00:00"
}
```

```http
GET /api/counselor/users/{user_id}/notes
Authorization: Bearer <counselor token>
```

返回咨询师对该用户的人工备注。

```http
POST /api/counselor/users/{user_id}/notes
Authorization: Bearer <counselor token>
Content-Type: application/json
```

请求：

```json
{
  "content": "下次咨询优先核实睡眠和近期压力源。"
}
```

```http
GET /api/counselor/users/{user_id}/trend
Authorization: Bearer <counselor token>
```

返回该用户已完成报告的主情绪、风险等级和置信度时间序列。

## 报告导出

```http
GET /api/reports/{task_id}/export?format=json
Authorization: Bearer <token>
```

```http
GET /api/reports/{task_id}/export?format=text
Authorization: Bearer <token>
```

导出 JSON 或纯文本报告。访问权限与 `GET /api/reports/{task_id}` 一致。

## 接口分组表

| 分组 | 接口 | 用途 |
| --- | --- | --- |
| 认证 | `/api/auth/register`, `/api/auth/jwt/login`, `/api/users/me` | 注册、登录、读取当前用户 |
| 普通用户 | `/api/videos/upload`, `/api/me/tasks`, `/api/me/counselors` | 上传视频、查看历史、查看授权咨询师、删除自己的历史任务 |
| 咨询师 | `/api/counselor/clients`, `/api/counselor/bindings`, `/api/counselor/users/{id}/history` | 管理绑定和查看用户历史 |
| 咨询辅助 | `/api/counselor/users/{id}/assistance-draft`, `/api/counselor/users/{id}/notes`, `/api/counselor/users/{id}/trend` | 生成辅助建议、记录备注、查看趋势 |
| 报告 | `/api/tasks/{task_id}`, `/api/reports/{task_id}`, `/api/reports/{task_id}/export` | 查询任务、查看报告、导出报告 |

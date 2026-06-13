import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Brain,
  CheckCircle2,
  Circle,
  Clock3,
  Download,
  FileText,
  FileVideo,
  Loader2,
  Link2,
  Mic2,
  LogOut,
  NotebookPen,
  Plus,
  ShieldCheck,
  Sparkles,
  Trash2,
  TrendingUp,
  Upload,
  UserRound,
  Users,
  Volume2,
  XCircle,
} from 'lucide-react';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STATUS_LABELS = {
  queued: '排队中',
  processing: '分析中',
  completed: '已完成',
  failed: '失败',
};

const STAGE_LABELS = {
  queued: '等待处理',
  preparing_video: '抽帧与音频提取',
  analyzing_face: '人脸表情分析',
  analyzing_speech: '语音转写与声学分析',
  fusing_features: '多模态融合',
  generating_advice: '专家意见生成',
  saving_report: '保存报告',
  completed: '分析完成',
  failed: '分析失败',
};

const TASK_STEPS = [
  { stage: 'queued', label: '上传' },
  { stage: 'preparing_video', label: '视频处理' },
  { stage: 'analyzing_face', label: '人脸分析' },
  { stage: 'analyzing_speech', label: '语音分析' },
  { stage: 'fusing_features', label: '融合判断' },
  { stage: 'generating_advice', label: '专家意见' },
  { stage: 'completed', label: '完成' },
];

const EMOTION_LABELS = {
  angry: '愤怒',
  disgust: '厌恶',
  fear: '恐惧',
  happy: '高兴',
  sad: '悲伤',
  surprise: '惊讶',
  neutral: '中性',
  unknown: '未知',
};

const RISK_LABELS = {
  low: '低',
  medium: '中',
  high: '高',
};

const AUTH_STORAGE_KEY = 'emotion-auth';

function App() {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY) || 'null');
    } catch {
      return null;
    }
  });
  const [file, setFile] = useState(null);
  const [task, setTask] = useState(null);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [authorizedCounselors, setAuthorizedCounselors] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [counselorDraft, setCounselorDraft] = useState('');
  const [counselorDraftAt, setCounselorDraftAt] = useState('');
  const [bindEmail, setBindEmail] = useState('');
  const [notes, setNotes] = useState([]);
  const [noteContent, setNoteContent] = useState('');
  const [trend, setTrend] = useState([]);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);

  const user = auth?.user || null;
  const token = auth?.access_token || '';
  const isBusy = isUploading || task?.status === 'processing' || task?.status === 'queued';
  const statusLabel = STATUS_LABELS[task?.status] || task?.status || '等待上传';
  const stageLabel = STAGE_LABELS[task?.stage] || task?.message || '等待上传';

  useEffect(() => {
    if (!token) return;
    apiFetch('/api/users/me')
      .then(async (response) => {
        if (!response.ok) throw new Error(await readError(response));
        return response.json();
      })
      .then((currentUser) => setAuth((current) => ({ ...current, user: currentUser })))
      .catch(() => signOut());
  }, []);

  useEffect(() => {
    if (!user) return;
    if (user.role === 'client') {
      loadMyTasks();
      loadMyCounselors();
    } else if (user.role === 'counselor') {
      loadCounselorClients();
    }
  }, [user?.id, user?.role]);

  async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  }

  async function signIn(payload) {
    setError('');
    const formData = new URLSearchParams();
    formData.set('username', payload.email);
    formData.set('password', payload.password);
    const response = await fetch(`${API_BASE_URL}/api/auth/jwt/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    const tokenData = await response.json();
    const userResponse = await fetch(`${API_BASE_URL}/api/users/me`, {
      headers: { Authorization: `Bearer ${tokenData.access_token}` },
    });
    if (!userResponse.ok) {
      throw new Error(await readError(userResponse));
    }
    const data = { ...tokenData, user: await userResponse.json() };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
    setAuth(data);
    setTask(null);
    setReport(null);
    setCounselorDraft('');
  }

  async function register(payload) {
    setError('');
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    await signIn({ email: payload.email, password: payload.password });
  }

  function signOut() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setAuth(null);
    setTask(null);
    setReport(null);
    setHistory([]);
    setClients([]);
    setSelectedClient(null);
    setCounselorDraft('');
  }

  async function loadMyTasks() {
    setIsLoadingWorkspace(true);
    try {
      const response = await apiFetch('/api/me/tasks');
      if (!response.ok) throw new Error(await readError(response));
      setHistory(await response.json());
    } catch (err) {
      setError(err.message || '读取历史失败');
    } finally {
      setIsLoadingWorkspace(false);
    }
  }

  async function loadMyCounselors() {
    try {
      const response = await apiFetch('/api/me/counselors');
      if (!response.ok) throw new Error(await readError(response));
      setAuthorizedCounselors(await response.json());
    } catch (err) {
      setError(err.message || '读取授权咨询师失败');
    }
  }

  async function loadCounselorClients() {
    setIsLoadingWorkspace(true);
    try {
      const response = await apiFetch('/api/counselor/clients');
      if (!response.ok) throw new Error(await readError(response));
      setClients(await response.json());
    } catch (err) {
      setError(err.message || '读取用户列表失败');
    } finally {
      setIsLoadingWorkspace(false);
    }
  }

  async function loadClientHistory(client) {
    setError('');
    setCounselorDraft('');
    setCounselorDraftAt('');
    const response = await apiFetch(`/api/counselor/users/${client.id}/history`);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const historyData = await response.json();
    setSelectedClient(historyData);
    await loadClientNotes(historyData.user_id);
    await loadClientTrend(historyData.user_id);
  }

  async function loadClientNotes(userId) {
    const response = await apiFetch(`/api/counselor/users/${userId}/notes`);
    if (response.ok) {
      setNotes(await response.json());
    }
  }

  async function loadClientTrend(userId) {
    const response = await apiFetch(`/api/counselor/users/${userId}/trend`);
    if (response.ok) {
      const data = await response.json();
      setTrend(data.points || []);
    }
  }

  async function createBinding(event) {
    event.preventDefault();
    setError('');
    const response = await apiFetch('/api/counselor/bindings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_email: bindEmail }),
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setBindEmail('');
    await loadCounselorClients();
  }

  async function deleteBinding(clientId) {
    setError('');
    const response = await apiFetch(`/api/counselor/bindings/${clientId}`, { method: 'DELETE' });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setSelectedClient(null);
    setNotes([]);
    setTrend([]);
    await loadCounselorClients();
  }

  async function createNote(event) {
    event.preventDefault();
    if (!selectedClient || !noteContent.trim()) return;
    setError('');
    const response = await apiFetch(`/api/counselor/users/${selectedClient.user_id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: noteContent }),
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setNoteContent('');
    await loadClientNotes(selectedClient.user_id);
  }

  async function generateCounselorDraft() {
    if (!selectedClient) return;
    setError('');
    setCounselorDraft('正在生成咨询师辅助建议...');
    const response = await apiFetch(`/api/counselor/users/${selectedClient.user_id}/assistance-draft`, {
      method: 'POST',
    });
    if (!response.ok) {
      setCounselorDraft('');
      setError(await readError(response));
      return;
    }
    const data = await response.json();
    setCounselorDraft(data.assistance);
    setCounselorDraftAt(data.generated_at || '');
    if (selectedClient) {
      await loadClientHistory({ id: selectedClient.user_id });
    }
  }

  async function uploadVideo(event) {
    event.preventDefault();
    if (!file) {
      setError('请选择一个视频文件');
      return;
    }

    setError('');
    setReport(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadResponse = await apiFetch('/api/videos/upload', {
        method: 'POST',
        body: formData,
      });
      if (!uploadResponse.ok) {
        throw new Error(await readError(uploadResponse));
      }

      const uploadData = await uploadResponse.json();
      setTask(uploadData);
      await pollTask(uploadData.task_id);
      await loadMyTasks();
    } catch (err) {
      setError(err.message || '上传失败');
    } finally {
      setIsUploading(false);
    }
  }

  async function pollTask(taskId) {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      const taskResponse = await apiFetch(`/api/tasks/${taskId}`);
      if (!taskResponse.ok) {
        throw new Error(await readError(taskResponse));
      }

      const taskData = await taskResponse.json();
      setTask(taskData);

      if (taskData.status === 'completed') {
        const reportResponse = await apiFetch(taskData.report_url);
        if (!reportResponse.ok) {
          throw new Error(await readError(reportResponse));
        }
        setReport(await reportResponse.json());
        return;
      }

      if (taskData.status === 'failed') {
        throw new Error(taskData.error || taskData.message || '任务分析失败');
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error('任务超时，请稍后查询结果');
  }

  async function openReport(taskItem) {
    setError('');
    const response = await apiFetch(`/api/reports/${taskItem.task_id}`);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setTask(taskItem);
    setReport(await response.json());
  }

  async function exportReport(format) {
    if (!report?.task_id) return;
    const response = await apiFetch(`/api/reports/${report.task_id}/export?format=${format}`);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `emotion-report-${report.task_id}.${format === 'json' ? 'json' : 'txt'}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!user) {
    return (
      <main className="app-shell">
        <section className="workspace auth-workspace">
          <header className="topbar">
            <div>
              <h1>多模态心理咨询辅助系统</h1>
              <p>普通用户上传交流视频获得非诊断性建议，心理咨询师查看授权用户历史并生成辅助工作草稿。</p>
            </div>
          </header>
          <AuthPanel onLogin={signIn} onRegister={register} error={error} setError={setError} />
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>多模态心理咨询辅助系统</h1>
            <p>{user.role === 'client' ? '上传交流视频后，系统会给出谨慎、非诊断性的辅助建议。' : '查看已关联用户的分析历史，并生成供专业人员参考的辅助工作草稿。'}</p>
          </div>
          <div className="session-actions">
            <div className="user-chip">
              {user.role === 'counselor' ? <ShieldCheck size={18} /> : <UserRound size={18} />}
              <span>{user.display_name || user.email}</span>
            </div>
            <StatusPill busy={isBusy || isLoadingWorkspace} status={user.role === 'client' ? statusLabel : '咨询师视图'} />
            <button className="icon-button" type="button" onClick={signOut} title="退出登录">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        {user.role === 'client' ? (
          <ClientWorkspace
            error={error}
            file={file}
            history={history}
            counselors={authorizedCounselors}
            isBusy={isBusy}
            onFileChange={setFile}
            onOpenReport={openReport}
            onSubmit={uploadVideo}
            stageLabel={stageLabel}
            statusLabel={statusLabel}
            task={task}
          />
        ) : (
          <CounselorWorkspace
            clients={clients}
            bindEmail={bindEmail}
            counselorDraft={counselorDraft}
            counselorDraftAt={counselorDraftAt}
            error={error}
            noteContent={noteContent}
            notes={notes}
            onCreateBinding={createBinding}
            onCreateNote={createNote}
            onDeleteBinding={deleteBinding}
            onGenerateDraft={generateCounselorDraft}
            onLoadHistory={loadClientHistory}
            onOpenReport={openReport}
            onSetBindEmail={setBindEmail}
            onSetNoteContent={setNoteContent}
            selectedClient={selectedClient}
            trend={trend}
          />
        )}

        {report ? <ReportView report={report} onExportReport={exportReport} /> : <EmptyReport task={task} />}
      </section>
    </main>
  );
}

function AuthPanel({ onLogin, onRegister, error, setError }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    email: 'client@example.com',
    password: 'client123',
    role: 'client',
    display_name: '',
  });
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (mode === 'login') {
        await onLogin({ email: form.email, password: form.password });
      } else {
        await onRegister(form);
      }
    } catch (err) {
      setError(err.message || '登录失败');
    } finally {
      setBusy(false);
    }
  }

  function fillDemo(role) {
    if (role === 'counselor') {
      setForm((current) => ({ ...current, email: 'counselor@example.com', password: 'counselor123', role }));
    } else {
      setForm((current) => ({ ...current, email: 'client@example.com', password: 'client123', role }));
    }
  }

  return (
    <section className="panel auth-panel">
      <div className="tabs">
        <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>登录</button>
        <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>注册</button>
      </div>
      <div className="demo-buttons">
        <button type="button" onClick={() => fillDemo('client')}>普通用户演示</button>
        <button type="button" onClick={() => fillDemo('counselor')}>咨询师演示</button>
      </div>
      <form onSubmit={submit} className="auth-form">
        <label>
          <span>账号/邮箱</span>
          <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        </label>
        <label>
          <span>密码</span>
          <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        </label>
        {mode === 'register' ? (
          <>
            <label>
              <span>角色</span>
              <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
                <option value="client">普通用户</option>
                <option value="counselor">心理咨询师</option>
              </select>
            </label>
            <label>
              <span>显示名称</span>
              <input value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} />
            </label>
          </>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? <Loader2 className="spin" size={18} /> : <ShieldCheck size={18} />}
          <span>{mode === 'login' ? '进入系统' : '创建账号'}</span>
        </button>
      </form>
      {error ? <ErrorBanner message={error} /> : null}
    </section>
  );
}

function ClientWorkspace({ counselors, error, file, history, isBusy, onFileChange, onOpenReport, onSubmit, stageLabel, statusLabel, task }) {
  return (
    <div className="main-grid">
      <section className="panel uploader">
        <div className="panel-heading">
          <FileVideo size={20} />
          <h2>视频上传</h2>
        </div>
        <form onSubmit={onSubmit}>
          <label className="drop-zone">
            <Upload size={28} />
            <span>{file ? file.name : '选择交流视频文件'}</span>
            <input type="file" accept="video/*" onChange={(event) => onFileChange(event.target.files?.[0] || null)} />
          </label>
          {file ? <FileMeta file={file} /> : null}
          <button type="submit" disabled={isBusy}>
            {isBusy ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
            <span>{isBusy ? '正在分析' : '开始分析'}</span>
          </button>
        </form>
        {error ? <ErrorBanner message={error} /> : null}
      </section>

      <TaskStatus task={task} statusLabel={statusLabel} stageLabel={stageLabel} />
      <HistoryPanel tasks={history} onOpenReport={onOpenReport} />
      <section className="panel history-list">
        <div className="panel-heading">
          <ShieldCheck size={20} />
          <h2>已授权咨询师</h2>
        </div>
        <div className="client-list">
          {counselors.map((counselor) => (
            <div className="list-row" key={counselor.id}>
              <span>{counselor.display_name || counselor.email}</span>
              <small>{counselor.email}</small>
            </div>
          ))}
          {!counselors.length ? <p className="muted">暂无授权咨询师</p> : null}
        </div>
      </section>
    </div>
  );
}

function CounselorWorkspace({
  bindEmail,
  clients,
  counselorDraft,
  counselorDraftAt,
  error,
  noteContent,
  notes,
  onCreateBinding,
  onCreateNote,
  onDeleteBinding,
  onGenerateDraft,
  onLoadHistory,
  onOpenReport,
  onSetBindEmail,
  onSetNoteContent,
  selectedClient,
  trend,
}) {
  return (
    <div className="main-grid counselor-grid">
      <section className="panel">
        <div className="panel-heading">
          <Users size={20} />
          <h2>关联用户</h2>
        </div>
        <form className="inline-form" onSubmit={onCreateBinding}>
          <input
            type="email"
            value={bindEmail}
            onChange={(event) => onSetBindEmail(event.target.value)}
            placeholder="输入普通用户邮箱"
          />
          <button type="submit">
            <Link2 size={18} />
            <span>绑定</span>
          </button>
        </form>
        <div className="client-list">
          {clients.map((client) => (
            <div className="client-row" key={client.id}>
              <button type="button" onClick={() => onLoadHistory(client)}>
                <span>{client.display_name || client.email}</span>
                <small>
                  {client.task_count} 次分析
                  {client.latest_risk_level ? ` · ${RISK_LABELS[client.latest_risk_level] || client.latest_risk_level}风险` : ''}
                </small>
              </button>
              <button className="icon-button" type="button" onClick={() => onDeleteBinding(client.id)} title="解除绑定">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          {!clients.length ? <p className="muted">暂无已关联用户</p> : null}
        </div>
        {error ? <ErrorBanner message={error} /> : null}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <FileText size={20} />
          <h2>{selectedClient ? `${selectedClient.display_name || selectedClient.email} 的历史` : '用户历史'}</h2>
        </div>
        {selectedClient ? (
          <>
            <HistoryPanel tasks={selectedClient.tasks} onOpenReport={onOpenReport} embedded />
            <button type="button" onClick={onGenerateDraft} disabled={!selectedClient.tasks.length}>
              <Sparkles size={18} />
              <span>生成咨询师辅助建议</span>
            </button>
            {counselorDraft ? (
              <div className="draft-box">
                {counselorDraftAt ? <small>生成时间：{new Date(counselorDraftAt).toLocaleString()}</small> : null}
                <p>{counselorDraft}</p>
              </div>
            ) : null}
            <TrendPanel trend={trend} />
            <NotesPanelForm
              noteContent={noteContent}
              notes={notes}
              onCreateNote={onCreateNote}
              onSetNoteContent={onSetNoteContent}
            />
          </>
        ) : (
          <p className="muted">选择左侧用户查看分析历史</p>
        )}
      </section>
    </div>
  );
}

function HistoryPanel({ tasks = [], onOpenReport, embedded = false }) {
  return (
    <section className={embedded ? 'history-list embedded' : 'panel history-list'}>
      {!embedded ? (
        <div className="panel-heading">
          <Clock3 size={20} />
          <h2>分析历史</h2>
        </div>
      ) : null}
      <div className="history-items">
        {tasks.map((item) => (
          <button key={item.task_id} type="button" onClick={() => item.report_url && onOpenReport(item)} disabled={!item.report_url}>
            <span>
              {item.created_at ? new Date(item.created_at).toLocaleString() : item.task_id}
              {item.dominant_emotion ? ` · ${emotionLabel(item.dominant_emotion)}` : ''}
            </span>
            <strong>{item.risk_level ? `${RISK_LABELS[item.risk_level] || item.risk_level}风险` : STATUS_LABELS[item.status] || item.status}</strong>
          </button>
        ))}
        {!tasks.length ? <p className="muted">暂无分析历史</p> : null}
      </div>
    </section>
  );
}

function TrendPanel({ trend = [] }) {
  return (
    <section className="sub-panel">
      <div className="panel-heading compact-heading">
        <TrendingUp size={18} />
        <h3>趋势摘要</h3>
      </div>
      <div className="trend-list">
        {trend.map((point) => (
          <div key={point.task_id}>
            <span>{point.created_at ? new Date(point.created_at).toLocaleDateString() : point.task_id}</span>
            <strong>{point.emotion ? emotionLabel(point.emotion) : '未知'} · {point.risk_level ? `${RISK_LABELS[point.risk_level] || point.risk_level}风险` : '未评估'}</strong>
          </div>
        ))}
        {!trend.length ? <p className="muted">暂无可展示趋势</p> : null}
      </div>
    </section>
  );
}

function NotesPanelForm({ noteContent, notes = [], onCreateNote, onSetNoteContent }) {
  return (
    <section className="sub-panel">
      <div className="panel-heading compact-heading">
        <NotebookPen size={18} />
        <h3>咨询备注</h3>
      </div>
      <form className="note-form" onSubmit={onCreateNote}>
        <textarea
          value={noteContent}
          onChange={(event) => onSetNoteContent(event.target.value)}
          placeholder="记录咨询师人工复核、沟通切入点或下次咨询关注事项"
        />
        <button type="submit">
          <Plus size={18} />
          <span>添加备注</span>
        </button>
      </form>
      <div className="note-list">
        {notes.map((note) => (
          <article key={note.id}>
            <small>{new Date(note.created_at).toLocaleString()}</small>
            <p>{note.content}</p>
          </article>
        ))}
        {!notes.length ? <p className="muted">暂无咨询备注</p> : null}
      </div>
    </section>
  );
}

function StatusPill({ busy, status }) {
  return (
    <div className="status-pill">
      {busy ? <Loader2 className="spin" size={18} /> : <Activity size={18} />}
      <span>{status}</span>
    </div>
  );
}

function FileMeta({ file }) {
  return (
    <dl className="compact-list">
      <div>
        <dt>文件大小</dt>
        <dd>{formatBytes(file.size)}</dd>
      </div>
      <div>
        <dt>文件类型</dt>
        <dd>{file.type || '未知'}</dd>
      </div>
    </dl>
  );
}

function TaskStatus({ task, statusLabel, stageLabel }) {
  const progress = Math.max(0, Math.min(task?.progress || 0, 100));

  return (
    <section className={`panel task-panel ${task?.status === 'failed' ? 'failed' : ''}`}>
      <div className="panel-heading">
        <CheckCircle2 size={20} />
        <h2>任务状态</h2>
      </div>

      <div className="progress-block">
        <div className="progress-meta">
          <strong>{stageLabel}</strong>
          <span>{progress}%</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <p>{task?.message || '上传视频后开始分析'}</p>
      </div>

      <ol className="step-list">
        {TASK_STEPS.map((step) => (
          <TaskStep key={step.stage} step={step} task={task} />
        ))}
      </ol>

      <dl className="status-list">
        <div>
          <dt>任务 ID</dt>
          <dd>{task?.task_id || '-'}</dd>
        </div>
        <div>
          <dt>当前状态</dt>
          <dd>{statusLabel}</dd>
        </div>
        <div>
          <dt>报告入口</dt>
          <dd>{task?.report_url || '-'}</dd>
        </div>
      </dl>

      {task?.error ? <ErrorBanner message={task.error} /> : null}
    </section>
  );
}

function TaskStep({ step, task }) {
  const currentIndex = TASK_STEPS.findIndex((item) => item.stage === task?.stage);
  const stepIndex = TASK_STEPS.findIndex((item) => item.stage === step.stage);
  const completed = task?.status === 'completed' || currentIndex > stepIndex;
  const active = task?.stage === step.stage && task?.status !== 'completed';
  const failed = task?.status === 'failed' && active;

  return (
    <li className={completed ? 'done' : failed ? 'failed' : active ? 'active' : ''}>
      {failed ? (
        <XCircle size={16} />
      ) : completed ? (
        <CheckCircle2 size={16} />
      ) : active ? (
        <Loader2 className="spin" size={16} />
      ) : (
        <Circle size={16} />
      )}
      <span>{step.label}</span>
    </li>
  );
}

function ErrorBanner({ message }) {
  return (
    <div className="error-banner">
      <AlertCircle size={18} />
      <span>{message}</span>
    </div>
  );
}

function EmptyReport({ task }) {
  return (
    <section className="empty-report">
      <Brain size={28} />
      <span>{task ? '任务完成后将在这里显示真实视频分析报告' : '上传视频后将在这里显示整段情绪预判和专家意见'}</span>
    </section>
  );
}

function ReportView({ report, onExportReport }) {
  const prediction = report.final_prediction;

  return (
    <section className="report-layout">
      <div className="report-actions">
        <button type="button" onClick={() => onExportReport('json')}>
          <Download size={18} />
          <span>导出 JSON</span>
        </button>
        <button type="button" onClick={() => onExportReport('text')}>
          <Download size={18} />
          <span>导出文本</span>
        </button>
      </div>
      <section className="summary-strip">
        <SummaryMetric icon={Clock3} label="视频时长" value={`${report.video_summary.duration_seconds}s`} />
        <SummaryMetric icon={FileVideo} label="抽帧数量" value={report.video_summary.frame_count || 0} />
        <SummaryMetric icon={Activity} label="检测人脸" value={report.video_summary.detected_faces} />
        <SummaryMetric icon={Mic2} label="语音检测" value={report.video_summary.speech_detected ? '有语音' : '无语音'} />
      </section>

      <section className="report-grid">
        <article className="panel prediction-panel">
          <div className="panel-heading">
            <Brain size={20} />
            <h2>综合预判</h2>
          </div>
          <div className={`prediction risk-${prediction.risk_level}`}>
            <strong>{emotionLabel(prediction.emotion)}</strong>
            <span>置信度 {formatPercent(prediction.confidence)}</span>
            <small>风险等级：{RISK_LABELS[prediction.risk_level] || prediction.risk_level}</small>
          </div>
          <ul className="evidence-list">
            {prediction.evidence.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <BarChart3 size={20} />
            <h2>人脸表情</h2>
          </div>
          <dl className="compact-list">
            <div>
              <dt>主导表情</dt>
              <dd>{emotionLabel(report.face_emotion.dominant)}</dd>
            </div>
            <div>
              <dt>有效帧数</dt>
              <dd>{report.face_emotion.analyzed_frames || report.video_summary.analyzed_frames || 0}</dd>
            </div>
            <div>
              <dt>跳过帧数</dt>
              <dd>{report.face_emotion.skipped_frames || report.video_summary.skipped_frames || 0}</dd>
            </div>
          </dl>
          <h3>平均概率</h3>
          <ProbabilityBars values={report.face_emotion.probabilities} />
          <h3>持续时长比例</h3>
          <ProbabilityBars values={report.face_emotion.duration_ratio} />
        </article>

        <article className="panel speech-panel">
          <div className="panel-heading">
            <Volume2 size={20} />
            <h2>语音特征</h2>
          </div>
          <dl className="feature-list">
            <div>
              <dt>语义情绪</dt>
              <dd>{emotionLabel(report.speech_features.semantic_emotion)}</dd>
            </div>
            <div>
              <dt>基频</dt>
              <dd>{report.speech_features.pitch_summary}</dd>
            </div>
            <div>
              <dt>语速</dt>
              <dd>{report.speech_features.speech_rate}</dd>
            </div>
            <div>
              <dt>清晰度</dt>
              <dd>{report.speech_features.clarity}</dd>
            </div>
            <div>
              <dt>语音标签</dt>
              <dd>{formatTags(report.speech_features.tags)}</dd>
            </div>
          </dl>
          <Transcript text={report.speech_features.transcript} />
          <AcousticDetails acoustic={report.speech_features.acoustic} />
        </article>

        <article className="panel advice-panel">
          <div className="panel-heading">
            <FileText size={20} />
            <h2>专家意见</h2>
          </div>
          <p>{report.expert_advice}</p>
        </article>

        <NotesPanel notes={report.video_summary.processing_notes} />
      </section>
    </section>
  );
}

function SummaryMetric({ icon: Icon, label, value }) {
  return (
    <article className="summary-metric">
      <Icon size={18} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function Transcript({ text }) {
  return (
    <div className="transcript">
      <h3>语音转写</h3>
      <p>{text || '未获得有效转写文本'}</p>
    </div>
  );
}

function AcousticDetails({ acoustic = {} }) {
  const rows = [
    ['采样率', acoustic.sample_rate ? `${acoustic.sample_rate} Hz` : '-'],
    ['音频时长', acoustic.duration_seconds ? `${acoustic.duration_seconds}s` : '-'],
    ['RMS 音量', formatNumber(acoustic.rms)],
    ['峰值', formatNumber(acoustic.peak)],
    ['过零率', formatNumber(acoustic.zero_crossing_rate)],
    ['有效发声比例', acoustic.voiced_ratio == null ? '-' : formatPercent(acoustic.voiced_ratio)],
    ['估计基频', acoustic.estimated_pitch_hz ? `${acoustic.estimated_pitch_hz} Hz` : '-'],
  ];

  return (
    <div className="acoustic-table">
      <h3>声学明细</h3>
      <dl>
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function NotesPanel({ notes = [] }) {
  if (!notes.length) return null;

  return (
    <article className="panel notes-panel">
      <div className="panel-heading">
        <AlertCircle size={20} />
        <h2>处理备注</h2>
      </div>
      <ul>
        {notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </article>
  );
}

function ProbabilityBars({ values = {} }) {
  const entries = Object.entries(values).sort((a, b) => b[1] - a[1]);
  return (
    <div className="bars">
      {entries.map(([emotion, value]) => (
        <div className="bar-row" key={emotion}>
          <span>{emotionLabel(emotion)}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
          </div>
          <strong>{formatPercent(value)}</strong>
        </div>
      ))}
    </div>
  );
}

async function readError(response) {
  try {
    const data = await response.json();
    return data.detail || JSON.stringify(data);
  } catch {
    return response.text();
  }
}

function emotionLabel(value) {
  return EMOTION_LABELS[value] || value || '未知';
}

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return '-';
  return Number(value).toFixed(4);
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatTags(tags = []) {
  return tags.length ? tags.join(', ') : '-';
}

createRoot(document.getElementById('root')).render(<App />);

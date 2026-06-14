import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertCircle,
  BarChart3,
  BookOpen,
  Brain,
  CheckCircle2,
  Circle,
  Clock3,
  CloudSun,
  Download,
  FileText,
  FileVideo,
  HeartPulse,
  Info,
  LayoutDashboard,
  Loader2,
  Link2,
  Mic2,
  LogOut,
  Moon,
  NotebookPen,
  Plus,
  Repeat2,
  ShieldCheck,
  Sparkles,
  Trash2,
  TrendingUp,
  Upload,
  UserRound,
  Users,
  Volume2,
  Wind,
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
const HERO_IMAGE = '/images/hero-counseling.png';
const EDUCATION_IMAGE = '/images/education-mental-health.png';

const VIEW_ITEMS = [
  { id: 'workspace', label: '工作台', icon: LayoutDashboard },
  { id: 'education', label: '心理科普', icon: BookOpen },
  { id: 'about', label: '项目说明', icon: Info },
];

const EDUCATION_TOPICS = [
  {
    title: '抑郁相关问题',
    icon: CloudSun,
    summary: '持续低落、兴趣下降和精力不足可能影响学习、工作与人际互动。',
    signs: ['持续情绪低落或空虚感', '兴趣减退、疲惫感增加', '睡眠、食欲或注意力明显变化'],
    impact: '可能造成效率下降、社交退缩、自我评价降低，并加重压力循环。',
    help: '建议记录情绪变化和生活事件，必要时联系心理咨询师或精神科医生进行专业评估。',
  },
  {
    title: '焦虑相关问题',
    icon: Wind,
    summary: '焦虑常表现为过度担心、紧张不安，也可能伴随心慌、出汗或呼吸急促。',
    signs: ['对未来事件反复担忧', '身体紧绷、心跳加快', '回避考试、社交或重要任务'],
    impact: '可能影响决策、睡眠和任务完成，使个体更难从压力情境中恢复。',
    help: '可先尝试规律作息、呼吸放松和任务拆分；若持续影响生活，应寻求专业帮助。',
  },
  {
    title: '睡眠问题',
    icon: Moon,
    summary: '入睡困难、早醒、睡眠浅或昼夜节律紊乱会显著影响情绪调节能力。',
    signs: ['难以入睡或反复醒来', '白天困倦、注意力下降', '睡前长期使用电子设备或反复思考压力事件'],
    impact: '长期睡眠不足会放大焦虑、低落和易怒感，并降低学习与工作效率。',
    help: '建议建立固定作息、减少睡前刺激；若严重失眠持续存在，应咨询专业人员。',
  },
  {
    title: '压力与适应问题',
    icon: Activity,
    summary: '学业、工作、人际或家庭变化都可能带来适应压力。',
    signs: ['容易烦躁或疲惫', '对任务失去控制感', '身体不适但难以找到明确原因'],
    impact: '压力长期累积可能影响情绪稳定、沟通质量和问题解决能力。',
    help: '可以梳理压力源、区分可控与不可控事项，并向可信任的人或咨询师寻求支持。',
  },
  {
    title: '创伤后应激相关问题',
    icon: ShieldCheck,
    summary: '经历强烈威胁或冲击事件后，个体可能出现反复回想、警觉升高或回避。',
    signs: ['反复想起相关画面或梦境', '对相似场景明显回避', '容易惊跳、警觉或情绪波动'],
    impact: '可能影响安全感、人际关系和日常功能，需要谨慎、稳定和专业的支持。',
    help: '不要强迫自己快速遗忘或独自处理；若症状明显，应尽快联系创伤知情的专业人员。',
  },
  {
    title: '强迫相关问题',
    icon: Repeat2,
    summary: '反复出现的想法或行为如果难以控制，并占用大量时间，可能带来明显困扰。',
    signs: ['反复检查、清洗或确认', '明知不必要却难以停止', '因仪式化行为影响学习、工作或生活'],
    impact: '可能使个体陷入短暂缓解与再次担忧的循环，逐渐扩大生活限制。',
    help: '建议记录触发情境和耗时程度，避免简单责备自己，并寻求专业评估与干预建议。',
  },
];

const URGENT_HELP_ITEMS = [
  '出现自伤或伤人想法，或担心自己无法保持安全。',
  '连续严重失眠、进食明显受影响，且已经影响基本生活。',
  '情绪或行为变化快速加重，身边人也明显感到担忧。',
  '学习、工作、人际或自我照护功能受到明显损害。',
];

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
  const [activeView, setActiveView] = useState('workspace');

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

  const viewTitle = activeView === 'education' ? '心理科普' : activeView === 'about' ? '项目说明' : '工作台';

  if (activeView === 'education') {
    return (
      <main className="app-shell">
        <section className="workspace">
          <SiteHeader
            activeView={activeView}
            onChangeView={setActiveView}
            user={user}
            onSignOut={signOut}
            status={user?.role === 'client' ? statusLabel : user ? '咨询师视图' : viewTitle}
            busy={isBusy || isLoadingWorkspace}
          />
          <EducationPage />
        </section>
      </main>
    );
  }

  if (activeView === 'about') {
    return (
      <main className="app-shell">
        <section className="workspace">
          <SiteHeader
            activeView={activeView}
            onChangeView={setActiveView}
            user={user}
            onSignOut={signOut}
            status={user?.role === 'client' ? statusLabel : user ? '咨询师视图' : viewTitle}
            busy={isBusy || isLoadingWorkspace}
          />
          <AboutPage />
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="app-shell">
        <section className="workspace">
          <SiteHeader activeView={activeView} onChangeView={setActiveView} status="未登录" />
          <HeroSection />
          <AuthPanel onLogin={signIn} onRegister={register} error={error} setError={setError} />
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <SiteHeader
          activeView={activeView}
          onChangeView={setActiveView}
          user={user}
          onSignOut={signOut}
          status={user.role === 'client' ? statusLabel : '咨询师视图'}
          busy={isBusy || isLoadingWorkspace}
        />
        <WorkspaceIntro user={user} history={history} clients={clients} task={task} />

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

function SiteHeader({ activeView = 'workspace', onChangeView, user, onSignOut, status, busy = false }) {
  return (
    <header className="site-header">
      <button className="brand-lockup" type="button" onClick={() => onChangeView?.('workspace')}>
        <span className="brand-mark"><Brain size={22} /></span>
        <span>
          <strong>MindScope</strong>
          <small>多模态心理咨询辅助系统</small>
        </span>
      </button>
      <nav className="site-nav" aria-label="站内导航">
        {VIEW_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              className={activeView === item.id ? 'active' : ''}
              onClick={() => onChangeView?.(item.id)}
            >
              <Icon size={17} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="session-actions">
        {user ? (
          <div className="user-chip">
            {user.role === 'counselor' ? <ShieldCheck size={18} /> : <UserRound size={18} />}
            <span>{user.display_name || user.email}</span>
          </div>
        ) : null}
        <StatusPill busy={busy} status={status || '就绪'} />
        {user ? (
          <button className="icon-button" type="button" onClick={onSignOut} title="退出登录">
            <LogOut size={18} />
          </button>
        ) : null}
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="hero-section">
      <div className="hero-copy">
        <span className="eyebrow"><HeartPulse size={16} /> 课程设计原型</span>
        <h1>多模态心理咨询辅助系统</h1>
        <p>
          系统结合视频表情、语音转写、声学特征和专家系统建议，为普通用户提供非诊断性反馈，
          并为心理咨询师整理可复核的用户历史与辅助工作草稿。
        </p>
        <div className="hero-points">
          <span><FileVideo size={17} /> 视频上传分析</span>
          <span><Users size={17} /> 咨询师授权查看</span>
          <span><ShieldCheck size={17} /> 非诊断性边界</span>
        </div>
      </div>
      <img src={HERO_IMAGE} alt="心理咨询辅助系统主视觉" />
    </section>
  );
}

function WorkspaceIntro({ user, history = [], clients = [], task }) {
  const isClient = user.role === 'client';
  const completed = history.filter((item) => item.status === 'completed').length;
  const failed = history.filter((item) => item.status === 'failed').length;
  const summaryItems = isClient
    ? [
        { label: '历史任务', value: history.length, icon: Clock3 },
        { label: '已完成报告', value: completed, icon: FileText },
        { label: '失败任务', value: failed, icon: AlertCircle },
      ]
    : [
        { label: '关联用户', value: clients.length, icon: Users },
        { label: '累计分析', value: clients.reduce((sum, item) => sum + (item.task_count || 0), 0), icon: BarChart3 },
        { label: '当前视图', value: '专业辅助', icon: ShieldCheck },
      ];

  return (
    <section className="workspace-intro">
      <div>
        <span className="eyebrow">{isClient ? '普通用户工作台' : '心理咨询师工作台'}</span>
        <h1>{isClient ? '上传交流视频，获取可复核的情绪分析报告' : '查看授权用户历史，生成咨询辅助草稿'}</h1>
        <p>
          {isClient
            ? '系统会展示处理阶段、主情绪、风险等级和专家建议。结果仅作心理健康沟通参考。'
            : '咨询师只能访问已绑定用户的历史数据，并可记录人工备注，最终判断仍由专业人员负责。'}
        </p>
      </div>
      <div className="stat-strip">
        {summaryItems.map((item) => {
          const Icon = item.icon;
          return (
            <article key={item.label}>
              <Icon size={18} />
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          );
        })}
      </div>
      {task?.status === 'failed' ? (
        <div className="retry-hint">
          <AlertCircle size={18} />
          <span>最近任务失败：{task.error || task.message || '请检查视频格式和模型服务状态后重新上传。'}</span>
        </div>
      ) : null}
    </section>
  );
}

function EducationPage() {
  return (
    <section className="education-page">
      <div className="education-hero">
        <div>
          <span className="eyebrow"><BookOpen size={16} /> 心理健康科普</span>
          <h1>常见心理问题的基础认识</h1>
          <p>
            本页用于课程展示和用户教育，帮助理解常见心理困扰的表现与求助方式。
            内容不构成诊断、治疗建议或危机干预方案。
          </p>
        </div>
        <img src={EDUCATION_IMAGE} alt="心理健康科普插图" />
      </div>

      <section className="notice-band">
        <ShieldCheck size={22} />
        <div>
          <strong>非诊断性声明</strong>
          <p>科普内容只用于心理健康教育。若出现持续痛苦、功能受损或安全风险，应联系专业人员或当地紧急服务。</p>
        </div>
      </section>

      <div className="topic-grid">
        {EDUCATION_TOPICS.map((topic) => (
          <EducationCard key={topic.title} topic={topic} />
        ))}
      </div>

      <section className="urgent-panel">
        <div className="panel-heading">
          <AlertCircle size={20} />
          <h2>何时应尽快求助</h2>
        </div>
        <ul>
          {URGENT_HELP_ITEMS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p>如果情况紧急，请优先联系当地紧急服务、医院急诊或可信任的身边人，系统输出不能替代即时帮助。</p>
      </section>
    </section>
  );
}

function EducationCard({ topic }) {
  const Icon = topic.icon;
  return (
    <article className="education-card">
      <div className="topic-icon"><Icon size={22} /></div>
      <h2>{topic.title}</h2>
      <p>{topic.summary}</p>
      <h3>常见表现</h3>
      <ul>
        {topic.signs.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <h3>可能影响</h3>
      <p>{topic.impact}</p>
      <h3>建议求助方式</h3>
      <p>{topic.help}</p>
      <small>系统边界：本卡片用于科普，不用于自我诊断或替代专业评估。</small>
    </article>
  );
}

function AboutPage() {
  return (
    <section className="about-page">
      <div className="about-header">
        <span className="eyebrow"><Info size={16} /> 项目说明</span>
        <h1>面向课程设计的多模态心理咨询辅助原型</h1>
        <p>
          项目采用前后端分离、模型服务解耦和数据库持久化架构，重点展示多模态数据处理、
          角色权限控制、报告可追溯和咨询师辅助工作流。
        </p>
      </div>
      <div className="about-grid">
        <article>
          <Brain size={24} />
          <h2>多模态分析</h2>
          <p>从视频中抽帧和提取音频，结合 DeepFace 表情分析、SenseVoice 语音转写与声学特征，再生成综合报告。</p>
        </article>
        <article>
          <ShieldCheck size={24} />
          <h2>角色与权限</h2>
          <p>普通用户只能查看自己的历史；心理咨询师只能查看已绑定用户，并可生成辅助建议和人工备注。</p>
        </article>
        <article>
          <FileText size={24} />
          <h2>论文与答辩资料</h2>
          <p>README 与 docs 中保留系统架构、API、演示脚本、小论文写作指南和 PPT 大纲，便于组员接手。</p>
        </article>
      </div>
    </section>
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
          {task?.status === 'failed' ? (
            <div className="retry-card">
              <AlertCircle size={18} />
              <span>上次分析失败，可重新选择视频后再次上传。</span>
            </div>
          ) : null}
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
                  {client.latest_task_at ? ` · ${new Date(client.latest_task_at).toLocaleDateString()}` : ''}
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
          <button key={item.task_id} type="button" className={item.status === 'failed' ? 'failed-row' : ''} onClick={() => item.report_url && onOpenReport(item)} disabled={!item.report_url}>
            <span>
              {item.created_at ? new Date(item.created_at).toLocaleString() : item.task_id}
              {item.dominant_emotion ? ` · ${emotionLabel(item.dominant_emotion)}` : ''}
              {item.error ? ` · ${item.error}` : ''}
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
          <div className="risk-rationale">
            <strong>风险依据</strong>
            <p>{riskRationale(prediction)}</p>
          </div>
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
          <div className="report-meta">
            <span>模型：{report.model_name || '本地兜底或未记录'}</span>
            <span>Prompt：{report.prompt_version || '未记录'}</span>
            <span>生成时间：{report.generated_at ? new Date(report.generated_at).toLocaleString() : '未记录'}</span>
          </div>
          <p>{report.expert_advice}</p>
          <div className="ethics-note">
            <ShieldCheck size={18} />
            <span>本报告仅供心理健康沟通和专业复核参考，不能替代诊断、治疗或危机干预。</span>
          </div>
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

function riskRationale(prediction) {
  const risk = RISK_LABELS[prediction.risk_level] || prediction.risk_level || '未知';
  const confidence = formatPercent(prediction.confidence);
  const evidence = prediction.evidence?.length ? `，并结合 ${prediction.evidence.length} 条可见证据` : '';
  return `系统根据主情绪“${emotionLabel(prediction.emotion)}”、置信度 ${confidence}${evidence} 给出${risk}风险提示。该等级用于提示复核优先级，不等同于医学诊断。`;
}

createRoot(document.getElementById('root')).render(<App />);

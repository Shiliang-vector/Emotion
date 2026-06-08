import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Brain,
  CheckCircle2,
  Circle,
  Clock3,
  FileText,
  FileVideo,
  Loader2,
  Mic2,
  Upload,
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

function App() {
  const [file, setFile] = useState(null);
  const [task, setTask] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const isBusy = isUploading || task?.status === 'processing' || task?.status === 'queued';
  const statusLabel = STATUS_LABELS[task?.status] || task?.status || '等待上传';
  const stageLabel = STAGE_LABELS[task?.stage] || task?.message || '等待上传';

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
      const uploadResponse = await fetch(`${API_BASE_URL}/api/videos/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!uploadResponse.ok) {
        throw new Error(await readError(uploadResponse));
      }

      const uploadData = await uploadResponse.json();
      setTask(uploadData);
      await pollTask(uploadData.task_id);
    } catch (err) {
      setError(err.message || '上传失败');
    } finally {
      setIsUploading(false);
    }
  }

  async function pollTask(taskId) {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      const taskResponse = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`);
      if (!taskResponse.ok) {
        throw new Error(await readError(taskResponse));
      }

      const taskData = await taskResponse.json();
      setTask(taskData);

      if (taskData.status === 'completed') {
        const reportResponse = await fetch(`${API_BASE_URL}${taskData.report_url}`);
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

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>人脸识别心情判别系统</h1>
            <p>上传交流视频后，系统会综合人脸表情、语音语义、声学特征和专家意见生成报告。</p>
          </div>
          <StatusPill busy={isBusy} status={statusLabel} />
        </header>

        <div className="main-grid">
          <section className="panel uploader">
            <div className="panel-heading">
              <FileVideo size={20} />
              <h2>视频上传</h2>
            </div>
            <form onSubmit={uploadVideo}>
              <label className="drop-zone">
                <Upload size={28} />
                <span>{file ? file.name : '选择交流视频文件'}</span>
                <input
                  type="file"
                  accept="video/*"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
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
        </div>

        {report ? <ReportView report={report} /> : <EmptyReport task={task} />}
      </section>
    </main>
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

function ReportView({ report }) {
  const prediction = report.final_prediction;

  return (
    <section className="report-layout">
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

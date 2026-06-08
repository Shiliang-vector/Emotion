import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertCircle,
  Brain,
  CheckCircle2,
  FileVideo,
  Loader2,
  Upload,
  Volume2,
} from 'lucide-react';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [file, setFile] = useState(null);
  const [task, setTask] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const statusLabel = useMemo(() => {
    if (!task) return '等待上传';
    const labels = {
      queued: '排队中',
      processing: '分析中',
      completed: '已完成',
      failed: '失败',
    };
    return labels[task.status] || task.status;
  }, [task]);

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
        throw new Error(await uploadResponse.text());
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
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const taskResponse = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`);
      if (!taskResponse.ok) {
        throw new Error(await taskResponse.text());
      }

      const taskData = await taskResponse.json();
      setTask(taskData);

      if (taskData.status === 'completed') {
        const reportResponse = await fetch(`${API_BASE_URL}${taskData.report_url}`);
        if (!reportResponse.ok) {
          throw new Error(await reportResponse.text());
        }
        setReport(await reportResponse.json());
        return;
      }

      if (taskData.status === 'failed') {
        throw new Error(taskData.error || '任务分析失败');
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
            <p>基于交流视频的人脸表情、语音语义、声学特征和专家意见综合分析</p>
          </div>
          <div className="status-pill">
            {isUploading || task?.status === 'processing' || task?.status === 'queued' ? (
              <Loader2 className="spin" size={18} />
            ) : (
              <Activity size={18} />
            )}
            <span>{statusLabel}</span>
          </div>
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
              <button type="submit" disabled={isUploading}>
                {isUploading ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
                <span>开始分析</span>
              </button>
            </form>
            {error ? (
              <div className="error-banner">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <CheckCircle2 size={20} />
              <h2>任务状态</h2>
            </div>
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
          </section>
        </div>

        {report ? <ReportView report={report} /> : <EmptyReport />}
      </section>
    </main>
  );
}

function EmptyReport() {
  return (
    <section className="empty-report">
      <Brain size={28} />
      <span>上传视频后将在这里显示整段情绪预判和专家意见</span>
    </section>
  );
}

function ReportView({ report }) {
  return (
    <section className="report-grid">
      <article className="panel metric-panel">
        <div className="panel-heading">
          <Brain size={20} />
          <h2>综合预判</h2>
        </div>
        <div className="prediction">
          <strong>{report.final_prediction.emotion}</strong>
          <span>置信度 {Math.round(report.final_prediction.confidence * 100)}%</span>
          <small>风险等级：{report.final_prediction.risk_level}</small>
        </div>
        <ul className="evidence-list">
          {report.final_prediction.evidence.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>

      <article className="panel">
        <div className="panel-heading">
          <Activity size={20} />
          <h2>人脸表情</h2>
        </div>
        <p className="dominant">主导表情：{report.face_emotion.dominant}</p>
        <ProbabilityBars values={report.face_emotion.probabilities} />
      </article>

      <article className="panel">
        <div className="panel-heading">
          <Volume2 size={20} />
          <h2>语音特征</h2>
        </div>
        <dl className="feature-list">
          <div>
            <dt>语义情绪</dt>
            <dd>{report.speech_features.semantic_emotion}</dd>
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
        </dl>
      </article>

      <article className="panel advice-panel">
        <div className="panel-heading">
          <Brain size={20} />
          <h2>专家意见</h2>
        </div>
        <p>{report.expert_advice}</p>
      </article>
    </section>
  );
}

function ProbabilityBars({ values }) {
  return (
    <div className="bars">
      {Object.entries(values).map(([emotion, value]) => (
        <div className="bar-row" key={emotion}>
          <span>{emotion}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
          </div>
          <strong>{Math.round(value * 100)}%</strong>
        </div>
      ))}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);


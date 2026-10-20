import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, AlertCircle, ArrowRight, BarChart3, BookOpen, CheckCircle2,
  Clock3, Database, FileSearch, FileText, Gauge, Layers3, Loader2,
  RefreshCw, Search, Send, ShieldCheck, SlidersHorizontal, Sparkles,
  Trash2, Upload, X
} from "lucide-react";
import "./styles.css";

const API = "/api";
const NAV_ITEMS = [
  { name: "Playground", icon: Sparkles, description: "Ask questions and inspect the RAG pipeline." },
  { name: "Knowledge Base", icon: Database, description: "Upload, index, inspect, and remove source documents." },
  { name: "Evaluation Lab", icon: BarChart3, description: "Review quality metrics across saved answers." },
  { name: "Runs", icon: FileText, description: "Open previous questions, answers, sources, and scores." }
];
const EMPTY_STATS = {
  documents: 0, chunks: 0, evaluations: 0,
  average_score: 0, groundedness: 0, average_latency_ms: 0
};
const ACCEPTED_EXTENSIONS = [".pdf", ".txt", ".md", ".markdown"];

function formatError(detail) {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || JSON.stringify(item)).join(" · ");
  }
  return "The request failed. Please try again.";
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(API + path, options);
  } catch {
    throw new Error("Cannot reach the backend. Check that the API is running and try Refresh.");
  }
  let data = {};
  try {
    data = await response.json();
  } catch {
    // Some gateway errors return HTML instead of JSON.
  }
  if (!response.ok) {
    throw new Error(formatError(data.detail) || "Request failed with status " + response.status + ".");
  }
  return data;
}

function formatBytes(value = 0) {
  if (value < 1024) return value + " B";
  if (value < 1048576) return Math.round(value / 1024) + " KB";
  return (value / 1048576).toFixed(1) + " MB";
}
function formatDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleString();
}
function scoreLabel(score) {
  if (score >= 90) return "Excellent";
  if (score >= 75) return "Good";
  if (score >= 60) return "Needs review";
  return "Poor";
}
function extensionOf(name = "") {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot).toLowerCase() : "";
}

function App() {
  const [active, setActive] = useState("Playground");
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.25);
  const [docs, setDocs] = useState([]);
  const [runs, setRuns] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [result, setResult] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [apiStatus, setApiStatus] = useState("Checking");

  const indexedDocs = useMemo(() => docs.filter((doc) => doc.status === "indexed"), [docs]);

  async function loadData() {
    const entries = await Promise.allSettled([
      api("/documents"),
      api("/evaluations"),
      api("/stats"),
      api("/health")
    ]);
    const labels = ["documents", "evaluations", "stats", "health"];
    const failures = [];
    entries.forEach((entry, index) => {
      if (entry.status === "rejected") {
        if (index !== 3) failures.push(labels[index] + ": " + entry.reason.message);
        if (index === 3) setApiStatus("Offline");
        return;
      }
      const value = entry.value;
      if (index === 0) setDocs(Array.isArray(value) ? value : []);
      if (index === 1) setRuns(Array.isArray(value) ? value : []);
      if (index === 2) setStats({ ...EMPTY_STATS, ...value });
      if (index === 3) setApiStatus(value?.status === "ok" ? "Connected" : "Unavailable");
    });
    if (failures.length) setError(failures.join(" "));
    else setError("");
    return failures.length === 0;
  }

  useEffect(() => {
    loadData();
  }, []);

  async function refresh() {
    setRefreshing(true);
    setNotice("");
    try {
      await loadData();
    } finally {
      setRefreshing(false);
    }
  }

  async function runPipeline(event) {
    event?.preventDefault();
    if (question.trim().length < 2) {
      setError("Enter a question with at least two characters.");
      return;
    }
    if (!indexedDocs.length) {
      setError("Upload and successfully index a document before running a question.");
      setActive("Knowledge Base");
      return;
    }
    setLoading(true);
    setError("");
    setNotice("");
    setResult(null);
    try {
      const output = await api("/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          top_k: topK,
          similarity_threshold: threshold
        })
      });
      setResult(output);
      setActive("Playground");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function uploadFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length || uploading) return;
    const invalid = files.filter((file) => !ACCEPTED_EXTENSIONS.includes(extensionOf(file.name)));
    if (invalid.length) {
      setError("Unsupported file type: " + invalid.map((file) => file.name).join(", ") + ". Use PDF, TXT, or Markdown.");
      return;
    }
    setUploading(true);
    setError("");
    setNotice("");
    let succeeded = 0;
    const failures = [];
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);
        try {
          await api("/documents/upload", { method: "POST", body: formData });
          succeeded += 1;
        } catch (err) {
          failures.push(file.name + ": " + err.message);
        }
      }
      await loadData();
      setActive("Knowledge Base");
      if (succeeded) setNotice("Successfully indexed " + succeeded + (succeeded === 1 ? " document." : " documents."));
      if (failures.length) setError(failures.join(" · "));
    } finally {
      setUploading(false);
    }
  }

  async function removeDocument(id) {
    const doc = docs.find((item) => item.id === id);
    if (!window.confirm("Delete " + (doc?.name || "this document") + " and remove its indexed chunks? This cannot be undone.")) return;
    setError("");
    setNotice("");
    try {
      await api("/documents/" + encodeURIComponent(id), { method: "DELETE" });
      if (result?.retrieved_context?.some((chunk) => chunk.document_id === id)) setResult(null);
      setNotice("Document deleted and its indexed chunks removed.");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  const activePage = NAV_ITEMS.find((item) => item.name === active) || NAV_ITEMS[0];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setActive("Playground"); }}>
          <span className="brand-mark">R</span>
          <span className="brand-copy"><strong>RAG Answer Eval</strong><small>Retrieval quality workspace</small></span>
        </a>
        <div className="nav-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map(({ name, icon: Icon }) => (
            <button key={name} type="button" onClick={() => { setActive(name); setError(""); setNotice(""); }}
              className={"nav-item" + (active === name ? " active" : "")} aria-current={active === name ? "page" : undefined}>
              <Icon size={18} strokeWidth={1.8} /><span>{name}</span>
              {name === "Runs" && runs.length > 0 && <span className="nav-count">{runs.length}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="backend-status">
            <span className={"status-dot " + (apiStatus === "Connected" ? "online" : apiStatus === "Checking" ? "checking" : "offline")} />
            <span><strong>Backend API</strong><small>{apiStatus === "Connected" ? "Connected and responding" : apiStatus === "Checking" ? "Checking connection…" : "Connection unavailable"}</small></span>
            <span className="status-text">{apiStatus}</span>
          </div>
          <div className="sidebar-note"><ShieldCheck size={16} /><span>Answers are grounded in indexed source documents.</span></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div className="page-heading">
            <div className="eyebrow">RETRIEVAL · GENERATION · EVALUATION</div>
            <h1>{activePage.name}</h1>
            <p>{activePage.description}</p>
          </div>
          <button className="button button-outline" type="button" onClick={refresh} disabled={refreshing}>
            {refreshing ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}
            {refreshing ? "Refreshing…" : "Refresh data"}
          </button>
        </header>

        {error && <div className="alert alert-error" role="alert"><AlertCircle size={17} /><span>{error}</span><button type="button" aria-label="Dismiss error" onClick={() => setError("")}><X size={15} /></button></div>}
        {notice && <div className="alert alert-success" role="status"><CheckCircle2 size={17} /><span>{notice}</span><button type="button" aria-label="Dismiss notice" onClick={() => setNotice("")}><X size={15} /></button></div>}

        <section className="stats-grid" aria-label="Workspace statistics">
          <StatCard icon={Database} label="Indexed documents" value={stats.documents} helper={stats.chunks + " searchable chunks"} />
          <StatCard icon={Gauge} label="Average quality" value={stats.evaluations ? stats.average_score + "/100" : "—"} helper={stats.evaluations + " saved evaluations"} />
          <StatCard icon={ShieldCheck} label="Faithfulness" value={stats.evaluations ? stats.groundedness + "%" : "—"} helper="Average context support score" />
          <StatCard icon={Activity} label="Average latency" value={stats.evaluations ? (stats.average_latency_ms / 1000).toFixed(2) + "s" : "—"} helper="Retrieval, generation and evaluation" />
        </section>

        {active === "Playground" && (
          <div className="playground-layout">
            <section className="card question-card">
              <div className="section-heading">
                <div><span className="section-kicker">ASK YOUR DATA</span><h2>Ask the knowledge base</h2><p>Get an answer with source passages and a quality report.</p></div>
                <span className="tag tag-blue"><Sparkles size={13} /> RAG pipeline</span>
              </div>
              <form onSubmit={runPipeline}>
                <label htmlFor="question" className="field-label">Your question</label>
                <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)}
                  placeholder="For example: What is the refund policy in the uploaded document?" maxLength={2000} />
                <div className="field-meta"><span>{question.length}/2000 characters</span><span>{indexedDocs.length} indexed document{indexedDocs.length === 1 ? "" : "s"} available</span></div>
                <div className="query-settings">
                  <div className="setting-control">
                    <label htmlFor="top-k"><SlidersHorizontal size={15} /> Retrieved chunks</label>
                    <select id="top-k" value={topK} onChange={(event) => setTopK(Number(event.target.value))}>
                      {[1, 3, 5, 7, 10].map((value) => <option key={value} value={value}>{value} chunks</option>)}
                    </select>
                  </div>
                  <div className="setting-control threshold-control">
                    <label htmlFor="threshold">Minimum relevance <strong>{threshold.toFixed(2)}</strong></label>
                    <input id="threshold" type="range" min="0" max="0.9" step="0.05" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} />
                    <span className="setting-hint">Lower values retrieve more results; higher values are stricter.</span>
                  </div>
                </div>
                <div className="form-actions">
                  <span className="hint-text"><BookOpen size={15} /> Uses only indexed source material</span>
                  <button className="button button-primary" type="submit" disabled={loading || !indexedDocs.length || question.trim().length < 2}>
                    {loading ? <><Loader2 size={16} className="spin" /> Running pipeline…</> : <><Send size={16} /> Run evaluation <ArrowRight size={15} /></>}
                  </button>
                </div>
              </form>
              {!indexedDocs.length && <div className="inline-empty"><Database size={18} /><span><strong>No indexed documents yet.</strong> Add a PDF, TXT, or Markdown file in Knowledge Base to start.</span><button type="button" onClick={() => setActive("Knowledge Base")}>Open Knowledge Base <ArrowRight size={14} /></button></div>}

              {result && <AnswerResult result={result} />}
            </section>
            <EvaluationPanel result={result} />
          </div>
        )}

        {active === "Knowledge Base" && <KnowledgeBase docs={docs} onUpload={uploadFiles} uploading={uploading} onDelete={removeDocument} />}
        {active === "Evaluation Lab" && <EvaluationLab runs={runs} stats={stats} />}
        {active === "Runs" && <RunsPage runs={runs} selectedRun={selectedRun} onSelect={setSelectedRun} />}
        <footer className="page-footer"><span>RAG Answer Eval</span><span>Quality scores are AI-generated signals; always review the source context.</span></footer>
      </main>
      {uploading && <div className="busy-banner"><Loader2 size={16} className="spin" /> Uploading and indexing document(s)…</div>}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, helper }) {
  return <article className="stat-card"><span className="stat-icon"><Icon size={17} /></span><span className="stat-label">{label}</span><strong className="stat-value">{value}</strong><small>{helper}</small></article>;
}

function AnswerResult({ result }) {
  const evaluation = result.evaluation || {};
  return <div className="answer-results">
    <div className="result-topline"><div><span className="section-kicker">PIPELINE RESULT</span><h3>Generated answer</h3></div><span className="score-pill"><CheckCircle2 size={15} /> {evaluation.overall_score ?? "—"}/100</span></div>
    <div className="pipeline-steps">
      {["Question", "Embeddings", "Vector search", "Gemini answer", "Quality check"].map((step, index) => <React.Fragment key={step}><span><CheckCircle2 size={13} />{step}</span>{index < 4 && <i>›</i>}</React.Fragment>)}
    </div>
    <div className="answer-box">{result.answer}</div>
    <div className="answer-meta"><span><Clock3 size={14} /> {result.latency_ms} ms total latency</span><span>{result.model}</span><span>Run #{result.evaluation_id}</span></div>
    <div className="source-section">
      <div className="subheading"><div><FileSearch size={17} /><h3>Retrieved source context</h3></div><span>{(result.retrieved_context || []).length} chunk(s)</span></div>
      {(result.retrieved_context || []).map((chunk) => <SourceCard key={chunk.id} source={chunk} />)}
      {!result.retrieved_context?.length && <p className="muted-text">No source context was returned.</p>}
    </div>
  </div>;
}

function EvaluationPanel({ result }) {
  const evaluation = result?.evaluation;
  const metrics = [
    ["Answer relevance", evaluation?.answer_relevance],
    ["Faithfulness", evaluation?.faithfulness],
    ["Context precision", evaluation?.context_precision],
    ["Completeness", evaluation?.completeness]
  ];
  return <section className="card evaluation-panel">
    <div className="section-heading"><div><span className="section-kicker">QUALITY REPORT</span><h2>Evaluation snapshot</h2><p>Scores from a separate model evaluation call.</p></div><BarChart3 size={21} className="heading-icon" /></div>
    {!evaluation ? <EmptyState icon={BarChart3} title="No evaluation yet" detail="Run a question to see relevance, faithfulness, precision, and completeness." /> :
      <>
        <div className="score-summary"><div className="score-circle" style={{ "--score": Math.max(0, Math.min(100, Number(evaluation.overall_score) || 0)) }}><div><strong>{evaluation.overall_score}</strong><span>out of 100</span></div></div><div className="score-caption"><strong>{evaluation.verdict || scoreLabel(evaluation.overall_score)}</strong><span>Overall answer quality</span></div></div>
        <div className="metric-bars">{metrics.map(([name, value]) => <MetricBar key={name} label={name} value={value} />)}</div>
        <div className="reasoning-box"><ShieldCheck size={17} /><div><strong>Evaluator reasoning</strong><p>{evaluation.reasoning || "No explanation was returned."}</p></div></div>
        {!!evaluation.issues?.length && <div className="issues-box"><div><AlertCircle size={16} /><strong>Potential issues</strong></div><ul>{evaluation.issues.map((issue, index) => <li key={index}>{issue}</li>)}</ul></div>}
        <p className="evaluation-disclaimer">These are model-generated assessments, not guaranteed ground truth.</p>
      </>}
  </section>;
}

function MetricBar({ label, value }) {
  const score = Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : 0;
  return <div className="metric-row"><div><span>{label}</span><strong>{value == null ? "—" : score + "%"}</strong></div><div className="metric-track"><span style={{ width: score + "%" }} /></div></div>;
}

function SourceCard({ source }) {
  return <article className="source-card">
    <div className="source-header"><strong><FileText size={15} />{source.document_name || "Source document"}</strong><span>{Math.round((Number(source.similarity) || 0) * 100)}% match</span></div>
    <div className="source-subheader"><span>Chunk {(Number(source.chunk_index) || 0) + 1}</span><span>{source.page_number ? "Page " + source.page_number : "Page not available"}</span></div>
    <p>{source.text || "Source text was not saved for this older run."}</p>
  </article>;
}

function EmptyState({ icon: Icon, title, detail }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={22} /></span><strong>{title}</strong><p>{detail}</p></div>;
}

function KnowledgeBase({ docs, onUpload, uploading, onDelete }) {
  const [dragging, setDragging] = useState(false);
  const [filter, setFilter] = useState("all");
  const indexedCount = docs.filter((doc) => doc.status === "indexed").length;
  const visibleDocs = docs.filter((doc) => filter === "all" || doc.status === filter);
  return <section className="card knowledge-card">
    <div className="section-heading">
      <div><span className="section-kicker">SOURCE MANAGEMENT</span><h2>Knowledge base</h2><p>Each indexed document is split into chunks for semantic search.</p></div>
      <label className={"button button-primary upload-button" + (uploading ? " is-disabled" : "")}><Upload size={16} />{uploading ? "Indexing…" : "Choose files"}<input type="file" accept=".pdf,.txt,.md,.markdown" multiple disabled={uploading} onChange={(event) => { onUpload(event.target.files); event.target.value = ""; }} /></label>
    </div>
    <div className={"upload-dropzone" + (dragging ? " drag-active" : "") + (uploading ? " drop-disabled" : "")}
      onDragOver={(event) => { event.preventDefault(); if (!uploading) setDragging(true); }}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }}
      onDrop={(event) => { event.preventDefault(); setDragging(false); if (!uploading) onUpload(event.dataTransfer.files); }}>
      <span className="upload-icon"><Upload size={22} /></span><strong>Drop files here to index them</strong>
      <p>PDF, TXT, and Markdown · up to the configured upload size · select multiple files</p>
      <span className="drop-note">Text is extracted, chunked, embedded, and stored in the vector database.</span>
    </div>
    <div className="list-toolbar"><div><h3>Documents <span>{docs.length}</span></h3><p>{indexedCount} successfully indexed · {docs.length - indexedCount} pending or failed</p></div>
      <label className="filter-label">Show <select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">All documents</option><option value="indexed">Indexed</option><option value="failed">Failed</option><option value="processing">Processing</option></select></label>
    </div>
    <div className="document-list">
      {visibleDocs.length ? visibleDocs.map((doc) => <article className="document-row" key={doc.id}>
        <span className="document-icon"><FileText size={19} /></span><div className="document-info"><strong title={doc.name}>{doc.name}</strong><small>{String(doc.file_type || "").toUpperCase()} · {formatBytes(doc.size_bytes)} · Added {formatDate(doc.created_at)}</small></div>
        <div className="document-chunks"><strong>{doc.chunks || 0}</strong><small>chunks</small></div>
        <span className={"status-badge status-" + (doc.status || "unknown")}>{doc.status || "unknown"}</span>
        <button type="button" className="icon-button danger-button" title={"Delete " + doc.name} aria-label={"Delete " + doc.name} onClick={() => onDelete(doc.id)}><Trash2 size={16} /></button>
      </article>) : <EmptyState icon={Database} title={filter === "all" ? "No documents yet" : "No matching documents"} detail={filter === "all" ? "Choose a file or drop one above. Your source text stays in your own workspace." : "Change the filter to see other document statuses."} />}
    </div>
    <div className="knowledge-footnote"><ShieldCheck size={15} /><span>Scanned image-only PDFs need OCR before their text can be indexed. Unsupported files and empty documents are rejected with an error.</span></div>
  </section>;
}

function EvaluationLab({ runs, stats }) {
  const metrics = [
    { label: "Overall quality", key: "overall_score", icon: Gauge },
    { label: "Answer relevance", key: "answer_relevance", icon: Search },
    { label: "Faithfulness", key: "faithfulness", icon: ShieldCheck },
    { label: "Context precision", key: "context_precision", icon: FileSearch },
    { label: "Completeness", key: "completeness", icon: CheckCircle2 }
  ];
  const average = (key) => runs.length ? Math.round(runs.reduce((sum, run) => sum + Number(run[key] || 0), 0) / runs.length) : 0;
  const avgLatency = runs.length ? Math.round(runs.reduce((sum, run) => sum + Number(run.latency_ms || 0), 0) / runs.length) : 0;
  return <div className="lab-layout">
    <section className="card">
      <div className="section-heading"><div><span className="section-kicker">AGGREGATED SCORES</span><h2>Answer quality metrics</h2><p>Calculated from the latest {runs.length} saved evaluation runs.</p></div><span className="tag">{runs.length} saved runs</span></div>
      {!runs.length ? <EmptyState icon={BarChart3} title="No evaluation data yet" detail="Run a question in Playground after indexing a document." /> :
        <div className="lab-metrics">{metrics.map(({ label, key, icon: Icon }) => <article className="lab-metric-card" key={key}><div className="lab-metric-title"><span className="small-icon"><Icon size={16} /></span><span>{label}</span></div><div className="lab-metric-value">{average(key)}<small>/100</small></div><MetricBar label="Average score" value={average(key)} /></article>)}</div>}
    </section>
    <section className="card">
      <div className="section-heading"><div><span className="section-kicker">RUN HEALTH</span><h2>Evaluation activity</h2><p>Operational indicators from saved pipeline executions.</p></div><Activity size={21} className="heading-icon" /></div>
      <div className="activity-grid"><div className="activity-stat"><span>Total saved evaluations</span><strong>{stats.evaluations}</strong><small>Recent runs are listed below</small></div><div className="activity-stat"><span>Average full-pipeline latency</span><strong>{runs.length ? (avgLatency / 1000).toFixed(2) + "s" : "—"}</strong><small>Includes retrieval, generation, and scoring</small></div></div>
      {!runs.length ? <EmptyState icon={Clock3} title="No activity to chart" detail="Your evaluations and latency summary will appear after the first run." /> :
        <div className="recent-outcomes"><div className="subheading"><div><Clock3 size={17} /><h3>Recent outcomes</h3></div><span>Latest {Math.min(runs.length, 5)}</span></div>
          {runs.slice(0, 5).map((run) => <div className="outcome-row" key={run.id}><div><strong>{run.question}</strong><small>{formatDate(run.created_at)} · {run.model}</small></div><div className="outcome-score"><strong>{run.overall_score}/100</strong><span>{run.verdict || scoreLabel(run.overall_score)}</span></div></div>)}
        </div>}
    </section>
  </div>;
}

function RunsPage({ runs, selectedRun, onSelect }) {
  return <section className="card runs-card">
    <div className="section-heading"><div><span className="section-kicker">SAVED HISTORY</span><h2>Pipeline runs</h2><p>Select a run to view the generated answer, evaluator reasoning, issue list, and saved sources.</p></div><span className="tag">{runs.length} latest runs</span></div>
    {!runs.length ? <EmptyState icon={FileText} title="No runs saved yet" detail="Ask a question in Playground. Completed evaluations are saved here automatically." /> :
      <div className="run-list">{runs.map((run) => {
        const opened = selectedRun?.id === run.id;
        const sources = Array.isArray(run.retrieved_documents) ? run.retrieved_documents : [];
        return <article className={"run-card" + (opened ? " run-open" : "")} key={run.id}>
          <button type="button" className="run-summary" aria-expanded={opened} onClick={() => onSelect(opened ? null : run)}>
            <span className="run-number">#{run.id}</span><span className="run-question"><strong>{run.question}</strong><small><Clock3 size={13} />{formatDate(run.created_at)} <span>·</span> {run.model}</small></span>
            <span className="run-score"><strong>{run.overall_score}/100</strong><small>{run.verdict || scoreLabel(run.overall_score)}</small></span>
            <span className="run-toggle">{opened ? <X size={17} /> : <ArrowRight size={17} />}</span>
          </button>
          {opened && <div className="run-detail">
            <div className="run-detail-answer"><h3>Generated answer</h3><p>{run.answer || "No answer was saved for this run."}</p></div>
            <div className="run-detail-metrics">{[
              ["Relevance", run.answer_relevance], ["Faithfulness", run.faithfulness],
              ["Context precision", run.context_precision], ["Completeness", run.completeness]
            ].map(([name, value]) => <div key={name}><small>{name}</small><strong>{value}%</strong><span className="metric-track"><span style={{ width: Math.max(0, Math.min(100, Number(value) || 0)) + "%" }} /></span></div>)}</div>
            <div className="reasoning-box"><ShieldCheck size={17} /><div><strong>Evaluator reasoning</strong><p>{run.reasoning || "No reasoning was saved."}</p></div></div>
            {!!run.issues?.length && <div className="issues-box"><div><AlertCircle size={16} /><strong>Potential issues</strong></div><ul>{run.issues.map((issue, index) => <li key={index}>{issue}</li>)}</ul></div>}
            <div className="source-section"><div className="subheading"><div><FileSearch size={17} /><h3>Saved source passages</h3></div><span>{sources.length} source(s)</span></div>
              {sources.length ? sources.map((source, index) => <SourceCard key={source.id || (String(run.id) + "-" + index)} source={source} />) : <p className="muted-text">No retrieved source details were saved for this run.</p>}
            </div>
            <div className="run-detail-footer"><span><Clock3 size={14} /> {run.latency_ms} ms</span><span>Model: {run.model}</span><span>Created {formatDate(run.created_at)}</span></div>
          </div>}
        </article>;
      })}</div>}
  </section>;
}

createRoot(document.getElementById("root")).render(<App />);

import { useEffect, useState, FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, Article, CompareResult, setToken } from "./api";

const KINDS = ["Editorial", "Opinion", "Essay", "Column", "Analysis", "Explainer"];

export function AuthPage() {
  const nav = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const r = await api<{ token: string }>(`/api/auth/${mode}`, { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(r.token);
      nav("/search");
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }

  return (
    <main className="auth">
      <h1 className="brand">Prep<span>Lens</span></h1>
      <p className="muted">Editorials from several publications, compared in one place.</p>
      <form onSubmit={submit}>
        <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" /></label>
        <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8}
          autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
        {err && <p className="error" role="alert">{err}</p>}
        <button className="primary" disabled={busy}>{busy ? "Please wait" : mode === "login" ? "Sign in" : "Create account"}</button>
      </form>
      <button className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
        {mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}
      </button>
    </main>
  );
}

function ArticleItem({ a, onToggle }: { a: Article; onToggle: (a: Article) => void }) {
  return (
    <article className="item">
      <div className="meta">{a.kind} · {a.exam}{a.is_demo && <b className="demo">DEMO DATA</b>}</div>
      <h3>{a.title}</h3>
      <div className="meta">By {a.author}, {a.publisher}, {a.published}</div>
      <p><span className="tag">{a.is_demo ? "Demo summary" : "AI summary"}</span> {a.summary}</p>
      <div className="meta">Perspective: {a.perspective}. Topics: {a.keywords.split(",").join(", ")}</div>
      <div className="actions">
        <a className="primary" href={a.url} target="_blank" rel="noopener noreferrer">Read original article</a>
        <button onClick={() => onToggle(a)} aria-pressed={a.bookmarked}>{a.bookmarked ? "Saved" : "Save"}</button>
        <Link to={`/compare?topic=${encodeURIComponent(a.topic)}`} className="btn">Compare</Link>
      </div>
    </article>
  );
}

type Results = { items: Article[]; total: number; page: number; page_size: number; publishers: string[] };

export function SearchPage() {
  const [text, setText] = useState("");
  const [f, setF] = useState({ q: "", kind: "", publisher: "", days: "", sort: "newest", page: 1 });
  const [data, setData] = useState<Results | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setStatus("loading");
    const p = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => v !== "" && p.set(k, String(v)));
    api<Results>(`/api/articles?${p}`).then(d => { setData(d); setStatus("ok"); }).catch(e => { setMsg(e.message); setStatus("error"); });
  }, [f]);

  const set = (patch: Partial<typeof f>) => setF(o => ({ ...o, page: 1, ...patch }));
  async function toggle(a: Article) {
    try {
      await api(`/api/bookmarks/${a.id}`, { method: a.bookmarked ? "DELETE" : "PUT" });
      setData(d => d && { ...d, items: d.items.map(i => (i.id === a.id ? { ...i, bookmarked: !i.bookmarked } : i)) });
    } catch (e) { setMsg((e as Error).message); }
  }
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <>
      <h1>Search</h1>
      <form className="searchbar" onSubmit={e => { e.preventDefault(); set({ q: text.trim() }); }}>
        <input value={text} onChange={e => setText(e.target.value)} placeholder="Search a topic, issue or keyword" aria-label="Search" />
        <button className="primary">Search</button>
      </form>
      <div className="filters">
        <label>Type<select value={f.kind} onChange={e => set({ kind: e.target.value })}><option value="">All</option>{KINDS.map(k => <option key={k}>{k}</option>)}</select></label>
        <label>Publisher<select value={f.publisher} onChange={e => set({ publisher: e.target.value })}><option value="">All</option>{data?.publishers.map(p => <option key={p}>{p}</option>)}</select></label>
        <label>Date<select value={f.days} onChange={e => set({ days: e.target.value })}><option value="">Any time</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option></select></label>
        <label>Sort<select value={f.sort} onChange={e => set({ sort: e.target.value })}><option value="newest">Newest</option><option value="oldest">Oldest</option></select></label>
      </div>
      {msg && <p className="error" role="alert">{msg}</p>}
      {status === "loading" && <p className="muted">Loading articles</p>}
      {status === "error" && <p className="error">Articles could not be loaded.</p>}
      {status === "ok" && data && (data.items.length === 0
        ? <p className="muted">No articles match. Try a broader topic or remove a filter.</p>
        : <>
            <p className="muted">{data.total} article{data.total === 1 ? "" : "s"}</p>
            {data.items.map(a => <ArticleItem key={a.id} a={a} onToggle={toggle} />)}
            <div className="actions">
              <button disabled={f.page <= 1} onClick={() => setF(o => ({ ...o, page: o.page - 1 }))}>Previous</button>
              <span className="muted">Page {f.page} of {pages}</span>
              <button disabled={f.page >= pages} onClick={() => setF(o => ({ ...o, page: o.page + 1 }))}>Next</button>
            </div>
          </>)}
    </>
  );
}

export function ComparePage() {
  const [sp, setSp] = useSearchParams();
  const topic = sp.get("topic") ?? "";
  const [topics, setTopics] = useState<{ topic: string; count: number }[]>([]);
  const [res, setRes] = useState<CompareResult | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { api<{ topic: string; count: number }[]>("/api/topics").then(setTopics).catch(e => setErr(e.message)); }, []);
  useEffect(() => {
    setRes(null); setErr("");
    if (!topic) return;
    setLoading(true);
    api<CompareResult>(`/api/compare?topic=${encodeURIComponent(topic)}`).then(setRes).catch(e => setErr(e.message)).finally(() => setLoading(false));
  }, [topic]);

  return (
    <>
      <h1>Compare viewpoints</h1>
      <label className="filters">Topic
        <select value={topic} onChange={e => setSp(e.target.value ? { topic: e.target.value } : {})}>
          <option value="">Choose a topic</option>
          {topics.map(t => <option key={t.topic} value={t.topic} disabled={t.count < 2}>{t.topic} ({t.count} articles{t.count < 2 ? ", needs 2 or more" : ""})</option>)}
        </select>
      </label>
      {err && <p className="error" role="alert">{err}</p>}
      {loading && <p className="muted">Comparing articles</p>}
      {!topic && !err && <p className="muted">Choose a topic that has at least two articles.</p>}
      {res && (
        <>
          <p className="notice">{res.label}</p>
          {res.common.length > 0 && <section><h2>Common ground</h2><ul>{res.common.map(c => <li key={c}>{c}</li>)}</ul></section>}
          <section><h2>By publication</h2>
            {res.perspectives.map(p => (
              <div className="item" key={p.publisher + p.author}>
                <h3>{p.publisher}{p.is_demo && <b className="demo">DEMO DATA</b>}</h3>
                <div className="meta">{p.author}. Perspective: {p.perspective}</div>
                <p>{p.summary}</p>
                <a href={p.url} target="_blank" rel="noopener noreferrer">Read original article</a>
              </div>
            ))}
          </section>
          {res.differences.length > 0 && <section><h2>Key differences</h2><ul>{res.differences.map(d => <li key={d}>{d}</li>)}</ul></section>}
          {res.synthesis && <section><h2>Balanced synthesis</h2><p>{res.synthesis}</p></section>}
        </>
      )}
    </>
  );
}

export function BookmarksPage() {
  const [items, setItems] = useState<Article[] | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api<Article[]>("/api/bookmarks").then(setItems).catch(e => setErr(e.message)); }, []);
  async function remove(a: Article) {
    try { await api(`/api/bookmarks/${a.id}`, { method: "DELETE" }); setItems(l => l && l.filter(i => i.id !== a.id)); }
    catch (e) { setErr((e as Error).message); }
  }
  return (
    <>
      <h1>Bookmarks</h1>
      {err && <p className="error" role="alert">{err}</p>}
      {items === null && !err && <p className="muted">Loading bookmarks</p>}
      {items?.length === 0 && <p className="muted">Nothing saved yet. Use Save on an article in Search.</p>}
      {items?.map(a => <ArticleItem key={a.id} a={a} onToggle={remove} />)}
    </>
  );
}

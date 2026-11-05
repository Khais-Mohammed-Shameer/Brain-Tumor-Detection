import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { Activity, ArrowRight, ArrowUpRight, BrainCircuit, Check, ChevronRight, CircleHelp, FileImage, FlaskConical, LoaderCircle, LockKeyhole, Menu, MoveUpRight, ScanLine, ShieldCheck, X } from 'lucide-react';
import Hero from './components/Hero';
import ScanViewer from './components/ScanViewer';
import ResultPanel from './components/ResultPanel';
import { decodeImage, loadOpenCV, preprocess } from './lib/preprocess';
import { attribution, loadEngine, predict } from './lib/inference';
import { MODEL_ID, SAMPLES, SOURCE } from './lib/types';
import type { Analysis, ImageView, Phase, SampleId, View } from './lib/types';

const Evidence = lazy(() => import('./components/Evidence'));
const ModelExplorer = lazy(() => import('./components/ModelExplorer'));
const nextFrame = () => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));

export default function App() {
  const [view, setView] = useState<View>('workspace');
  const [phase, setPhase] = useState<Phase>('idle');
  const [analysis, setAnalysis] = useState<Analysis>();
  const [filename, setFilename] = useState('');
  const [error, setError] = useState<string>();
  const [imageView, setImageView] = useState<ImageView>('original');
  const [heatmap, setHeatmap] = useState<string>();
  const [heatmapBusy, setHeatmapBusy] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string>();
  const [engineState, setEngineState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [history, setHistory] = useState<Analysis[]>([]);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [offlineReady, setOfflineReady] = useState(false);
  const working = useRef(false);
  const fetchingSample = useRef(false);
  const heatmapVersion = useRef(0);
  const urls = useRef(new Set<string>());
  const busy = !['idle', 'complete', 'error'].includes(phase);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      Promise.all([loadEngine(), loadOpenCV()]).then(() => { if (!cancelled) setEngineState('ready'); }).catch(() => { if (!cancelled) setEngineState('error'); });
    }, 250);
    const trackedUrls = urls.current;
    return () => { cancelled = true; clearTimeout(timer); trackedUrls.forEach(url => URL.revokeObjectURL(url)); };
  }, []);

  useEffect(() => {
    if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
    let cancelled = false;
    navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready)
      .then(() => { if (!cancelled) setOfflineReady(true); }).catch(() => { /* The online studio remains fully usable. */ });
    return () => { cancelled = true; };
  }, []);

  function navigate(next: View) {
    setView(next); setMobileMenu(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function analyze(file: File, sample?: SampleId) {
    if (working.current) return;
    working.current = true;
    heatmapVersion.current++;
    const start = performance.now();
    setAnalysis(undefined); setError(undefined); setHeatmap(undefined); setHeatmapError(undefined); setHeatmapBusy(false);
    setImageView('original'); setFilename(file.name); setPhase('validating');
    let url: string | undefined;
    try {
      const decoded = await decodeImage(file); url = decoded.url;
      setPhase('loading');
      await Promise.all([loadEngine(), loadOpenCV()]); setEngineState('ready');
      setPhase('preprocessing'); await nextFrame();
      const processed = await preprocess(decoded.image);
      setPhase('inference'); await nextFrame();
      const prediction = await predict(processed.values);
      const bytes = await file.arrayBuffer();
      const hash = crypto.subtle ? Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(x => x.toString(16).padStart(2, '0')).join('') : 'unavailable';
      const result: Analysis = { id: crypto.randomUUID().slice(0, 8), filename: file.name, imageUrl: url, sample,
        ...prediction, label: prediction.score > 0.5 ? 'tumor' : 'no-tumor', processed,
        elapsed: performance.now() - start, timestamp: new Date().toISOString(), hash };
      urls.current.add(url);
      setAnalysis(result); setPhase('complete');
      setHistory(previous => {
        const next = [result, ...previous].slice(0, 5);
        for (const old of previous.slice(4)) { URL.revokeObjectURL(old.imageUrl); urls.current.delete(old.imageUrl); }
        return next;
      });
    } catch (caught) {
      if (url) URL.revokeObjectURL(url);
      setError(caught instanceof Error ? caught.message : 'This image could not be analyzed. Try another image.');
      setPhase('error');
    } finally { working.current = false; }
  }

  async function loadSample(id: SampleId) {
    if (working.current || fetchingSample.current) return;
    const sample = SAMPLES.find(s => s.id === id)!;
    fetchingSample.current = true;
    heatmapVersion.current++;
    setAnalysis(undefined); setError(undefined); setHeatmap(undefined); setHeatmapError(undefined); setHeatmapBusy(false);
    setImageView('original'); setFilename(sample.name);
    setPhase('loading');
    try {
      const response = await fetch(sample.src);
      if (!response.ok) throw new Error('The reference image could not load. Try again.');
      const blob = await response.blob();
      await analyze(new File([blob], sample.name, { type: 'image/jpeg' }), id);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'The reference image could not load.'); setPhase('error'); }
    finally { fetchingSample.current = false; }
  }

  async function showAttribution() {
    if (!analysis || working.current || heatmapBusy) return;
    setImageView('attention');
    if (heatmap) return;
    const version = ++heatmapVersion.current;
    setHeatmapBusy(true); setHeatmapError(undefined);
    try {
      await nextFrame();
      const map = await attribution(analysis.processed.values, analysis.label === 'tumor');
      if (version === heatmapVersion.current) setHeatmap(map);
    } catch {
      if (version === heatmapVersion.current) setHeatmapError('Attribution is unavailable on this device. The prediction is unchanged. Try the model-input view.');
    } finally { if (version === heatmapVersion.current) setHeatmapBusy(false); }
  }

  function clear() { if (working.current) return; heatmapVersion.current++; setAnalysis(undefined); setError(undefined); setPhase('idle'); setImageView('original'); setHeatmap(undefined); setHeatmapBusy(false); }

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header"><div className="header-inner">
      <a className="brand" href="#" onClick={event => { event.preventDefault(); navigate('workspace'); }} aria-label="C.A.R.E. home"><img src="/favicon.svg" alt="" width="35" height="35" /><span>C.A.R.E.<small>MRI RESEARCH STUDIO</small></span></a>
      <nav className={mobileMenu ? 'nav-open' : ''} aria-label="Main navigation">{[['workspace', 'Workspace'], ['evidence', 'Evidence'], ['model', 'Inside the model']].map(([id, label]) => <button key={id} className={view === id ? 'nav-active' : ''} onClick={() => navigate(id as View)} aria-current={view === id ? 'page' : undefined}>{label}{view === id ? <span /> : null}</button>)}</nav>
      <div className="header-right"><span className="local-badge"><LockKeyhole size={12} /> BROWSER-LOCAL</span><button className="icon-button help-button" onClick={() => navigate('model')} aria-label="How the model works"><CircleHelp size={19} /></button><button className="icon-button menu-button" aria-label={mobileMenu ? 'Close navigation' : 'Open navigation'} aria-expanded={mobileMenu} onClick={() => setMobileMenu(v => !v)}>{mobileMenu ? <X size={21} /> : <Menu size={21} />}</button></div>
    </div></header>
    <main id="main" className="main-container">
      {view === 'workspace' ? <div className="page-enter">
        <Hero onExplore={() => navigate('model')} />
        <div className="spec-strip"><div><span>01</span><strong>IMAGE IN. INSIGHT OUT.</strong></div><p><i /> 240 × 240 INPUT</p><p><i /> 11,137 PARAMETERS</p><p><i /> EXPLAINABLE PIPELINE</p><span className="research-pill"><FlaskConical size={12} /> RESEARCH PROTOTYPE</span></div>
        <section id="workspace" className="workspace-section" aria-labelledby="workspace-title"><div className="section-heading workspace-heading"><div><div className="eyebrow">01 / THE WORKSPACE</div><h2 id="workspace-title">Your image. Under the lens.</h2></div><div className="engine-status" role="status"><span className={`status-dot ${engineState}`} />{engineState === 'ready' ? 'Research engine ready' : engineState === 'loading' ? 'Preparing research engine' : 'Engine will retry on analysis'}</div></div>
          <div className="workspace-grid"><ScanViewer key={analysis?.id || 'empty'} analysis={analysis} phase={phase} filename={filename} busy={busy} error={error} onFile={analyze} onSample={loadSample} onClear={clear} onAttribution={showAttribution} imageView={imageView} setImageView={setImageView} heatmap={heatmap} heatmapBusy={heatmapBusy} heatmapError={heatmapError} /><ResultPanel analysis={analysis} phase={phase} onEvidence={() => navigate('evidence')} /></div>
          <div className="sample-strip"><div className="sample-intro"><span className="eyebrow">START WITH A REFERENCE</span><p>Two examples. One visible process.</p></div><div className="sample-buttons">{SAMPLES.map(sample => <button key={sample.id} className={`sample-button ${analysis?.sample === sample.id ? 'sample-selected' : ''}`} onClick={() => loadSample(sample.id)} disabled={busy}><img src={sample.src} alt="" /><div><strong>{sample.title}<span>{analysis?.sample === sample.id ? <Check size={11} /> : null}</span></strong><small>{sample.label}</small></div><ArrowUpRight size={17} /></button>)}</div><p className="sample-disclaimer">Source dataset examples.<br />Not an independent test.</p></div>
          {analysis ? <div className="analysis-meta"><span><FileImage size={12} /> {analysis.filename}</span><span>{analysis.processed.crop.width} × {analysis.processed.crop.height} CROP</span><span>{Math.round(analysis.elapsed)} MS TOTAL</span><span>{analysis.backend.toUpperCase()} / LOCAL</span></div> : null}
        </section>
        {history.length > 1 ? <section className="session-section"><div className="session-heading"><span className="eyebrow">THIS SESSION</span><span className="mono dim">IN MEMORY ONLY · LAST 5 IMAGES</span></div><div className="history-list">{history.map(item => <button key={item.id} className={analysis?.id === item.id ? 'history-active' : ''} disabled={busy} onClick={() => { heatmapVersion.current++; setAnalysis(item); setPhase('complete'); setError(undefined); setImageView('original'); setHeatmap(undefined); setHeatmapError(undefined); setHeatmapBusy(false); }}><img src={item.imageUrl} alt="" /><span>{item.filename}</span><small>{(item.score * 100).toFixed(2)} / 100</small><ChevronRight size={14} /></button>)}</div></section> : null}
        <section className="three-principles">{[
          [ShieldCheck, 'Private by design.', 'Images stay on your device. The model runs right here in your browser.'],
          [ScanLine, 'Every step, visible.', 'Inspect the crop, the model input and a computed attribution map.'],
          [BrainCircuit, 'Evidence before claims.', 'A credited reference model, transparent limits and no invented accuracy.'],
        ].map(([Icon, title, text]) => { const Graphic = Icon as typeof ShieldCheck; return <article key={title as string}><Graphic size={21} strokeWidth={1.3} /><div><h3>{title as string}</h3><p>{text as string}</p></div></article>; })}</section>
        <section className="bottom-callout"><div><span className="eyebrow">THE MOST INTERESTING PART?</span><h2>Understanding why.</h2><p>A prediction starts the conversation. The evidence makes it meaningful.</p></div><button className="outline-button" onClick={() => navigate('evidence')}>Explore the evidence <MoveUpRight size={17} /></button></section>
      </div> : <Suspense fallback={<div className="page-loading" role="status"><LoaderCircle className="spin" /> Opening the research view…</div>}>{view === 'evidence' ? <Evidence onWorkspace={() => navigate('workspace')} /> : <ModelExplorer analysis={analysis} onWorkspace={() => navigate('workspace')} />}</Suspense>}
    </main>
    <footer className="site-footer"><div className="footer-top"><a className="footer-brand" href="#" onClick={event => { event.preventDefault(); navigate('workspace'); }}>C.A.R.E.<span>Curiosity, with clarity.</span></a><div><a href={SOURCE} target="_blank" rel="noreferrer">Model & source credits <ArrowUpRight size={13} /></a><button onClick={() => navigate('evidence')}>Evidence & limitations <ArrowRight size={13} /></button></div></div><div className="footer-bottom"><p><Activity size={12} /> Experimental image classification. For education and research. Not a medical diagnosis.</p><span>{offlineReady ? 'OFFLINE READY' : MODEL_ID.toUpperCase()} <i /> V1.0</span></div></footer>
  </div>;
}

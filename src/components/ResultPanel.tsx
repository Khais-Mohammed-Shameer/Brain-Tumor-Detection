import { Activity, ArrowUpRight, Check, Download, Fingerprint, ShieldCheck } from 'lucide-react';
import type { Analysis, Phase } from '../lib/types';
import { exportAnalysis } from '../lib/export';

export default function ResultPanel({ analysis, phase, onEvidence }: { analysis?: Analysis; phase: Phase; onEvidence: () => void }) {
  const favored = analysis?.label === 'tumor';
  const nearThreshold = analysis && Math.abs(analysis.score - 0.5) < 0.15;
  return <aside className="result-panel panel" aria-label="Model result" aria-live="polite">
    <div className="panel-header"><div className="panel-title"><Activity size={14} /><span>MODEL OUTPUT</span></div><span className={`small-tag ${analysis ? 'tag-live' : ''}`}>{analysis ? 'COMPLETE' : 'STANDBY'}</span></div>
    <div className={`result-body ${favored ? 'result-positive' : ''}`}>
      {analysis ? <>
        <div className="result-topline"><span className="eyebrow">EXPERIMENTAL CLASSIFICATION</span><span className="mono">{analysis.inferenceMs < 1000 ? `${Math.round(analysis.inferenceMs)} MS` : `${(analysis.inferenceMs / 1000).toFixed(1)} S`}</span></div>
        <div className="result-verdict"><span className={`verdict-symbol ${favored ? 'positive' : ''}`}>{favored ? <FocusMark /> : <Check size={22} strokeWidth={1.5} />}</span><div><h3>{favored ? 'Tumor label favored' : 'No-tumor label favored'}</h3><p>{nearThreshold ? 'The score is close to the decision threshold.' : 'A prediction about this image, not a diagnosis.'}</p></div></div>
        <div className="score-block"><span className="score-label">TUMOR-CLASS SCORE</span><div className="score-value" data-score={analysis.score}>{(analysis.score * 100).toFixed(2)}<span>/ 100</span></div><div className="score-track"><span className="score-fill" style={{ width: `${Math.max(0.4, analysis.score * 100)}%` }} /><i className="threshold-mark" /></div><div className="score-axis"><span>NO-TUMOR LABEL</span><span>50</span><span>TUMOR LABEL</span></div><p>Raw model score. It is not a calibrated probability of disease.</p></div>
        <div className="result-checks"><span><ShieldCheck size={15} /> Basic image checks passed <Check size={13} /></span><span><Fingerprint size={15} /> Reference model verified <Check size={13} /></span></div>
        {analysis.sample ? <div className="reference-note"><strong>REFERENCE EXAMPLE</strong><p>This image comes from the source model’s dataset. It demonstrates the pipeline; it is not an independent accuracy test.</p></div> : <div className="reference-note"><strong>INTERPRET WITH CONTEXT</strong><p>Image checks do not establish MRI identity. Performance on new images has not been independently measured.</p></div>}
        <button className="export-button" onClick={() => exportAnalysis(analysis)}><Download size={15} /> Export research record <ArrowUpRight size={15} /></button>
      </> : <>
        <div className="standby-art"><span /><span /><span /><Activity size={27} strokeWidth={1} /></div>
        <h3>{phase === 'error' ? 'A clearer image, please.' : phase === 'idle' ? 'A signal, with context.' : 'Following the signal.'}</h3>
        <p className="standby-copy">{phase === 'error' ? 'The input was rejected before classification. Try a reference image or choose a different file.' : 'Analyze an image to explore the model’s prediction, its input, and the evidence behind it.'}</p>
        <div className="standby-steps"><span><i>01</i> Check image quality</span><span><i>02</i> Prepare the model input</span><span><i>03</i> Inspect the prediction</span></div>
        <div className="standby-note"><ShieldCheck size={17} /><p><strong>Research, made transparent.</strong><br />No clinical accuracy claim. No hidden image uploads.</p></div>
      </>}
    </div>
    <button className="result-footer" onClick={onEvidence}><span>Know the model. Know its limits.</span><ArrowUpRight size={15} /></button>
  </aside>;
}

function FocusMark() { return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /></svg>; }

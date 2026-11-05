import { ArrowRight, ArrowUpRight, ChevronRight, CircleHelp, Layers3 } from 'lucide-react';
import { useState } from 'react';
import type { Analysis } from '../lib/types';

const steps = [
  { n: '01', title: 'Read the image', detail: 'A single JPG or PNG enters the pipeline. Basic checks reject unreadable files, very small images, near-blank inputs and obvious high-frequency noise. These checks do not prove that an image is an MRI.', shape: 'JPG / PNG → BGR PIXELS', tag: 'DECODE + QUALITY CHECKS' },
  { n: '02', title: 'Find the foreground', detail: 'A grayscale copy is blurred, thresholded at 45, eroded and dilated. The largest external contour defines a crop. This is a simple foreground heuristic; it does not detect a tumor or reliably segment brain anatomy.', shape: 'LARGEST CONTOUR → CROP', tag: 'THRESHOLD-BASED CROP' },
  { n: '03', title: 'Build the model input', detail: 'The crop is resized with cubic interpolation to 240 × 240 pixels. Channels remain in BGR order to match training, and values are divided by 255. The same preprocessing must be used for training and prediction.', shape: '240 × 240 × 3 · VALUES 0–1', tag: 'RESIZE + NORMALIZE' },
  { n: '04', title: 'Follow the network', detail: 'Thirty-two learned 7 × 7 filters extract image patterns. Batch normalization and ReLU transform these features. Two pooling layers reduce their spatial size, then a dense layer produces one score.', shape: '11,137 PARAMETERS · 1 OUTPUT', tag: 'CONVOLUTIONAL NEURAL NETWORK' },
  { n: '05', title: 'Question the output', detail: 'A sigmoid maps the final value to 0–1. A threshold of 0.5 selects the favored label. Grad-CAM can show spatial influence on the predicted class. Neither a high score nor a heatmap establishes a medical diagnosis.', shape: 'SCORE → LABEL · THRESHOLD 0.5', tag: 'CLASSIFICATION + ATTRIBUTION' },
];

export default function ModelExplorer({ analysis, onWorkspace }: { analysis?: Analysis; onWorkspace: () => void }) {
  const [selected, setSelected] = useState(0);
  const step = steps[selected];
  const sourceWidth = analysis?.processed.quality.width || 180;
  const sourceHeight = analysis?.processed.quality.height || 218;
  const crop = analysis?.processed.crop || { x: 20, y: 25, width: 137, height: 165 };
  return <div className="page-enter model-page">
    <div className="page-heading"><div className="eyebrow"><span className="tiny-cross">+</span> 03 / INSIDE THE MODEL</div><h1>Follow the image.<br /><span>Understand the signal.</span></h1><p>No mystery box. Explore each step between an image<br />and a prediction, one decision at a time.</p></div>
    <section className="model-explorer panel">
      <div className="explorer-steps" role="tablist" aria-label="Processing pipeline">{steps.map((s, i) => <button key={s.n} role="tab" id={`step-${i}`} aria-controls="step-content" aria-selected={selected === i} onClick={() => setSelected(i)} onKeyDown={event => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowRight') { event.preventDefault(); setSelected((selected + 1) % steps.length); (document.getElementById(`step-${(selected + 1) % steps.length}`) as HTMLButtonElement)?.focus(); }
        if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') { event.preventDefault(); setSelected((selected + steps.length - 1) % steps.length); (document.getElementById(`step-${(selected + steps.length - 1) % steps.length}`) as HTMLButtonElement)?.focus(); }
      }}><span>{s.n}</span><strong>{s.title}</strong><ChevronRight size={15} /></button>)}</div>
      <div className="explorer-content" role="tabpanel" id="step-content" aria-labelledby={`step-${selected}`}><div className="explorer-text"><span className="eyebrow">{step.tag}</span><h2>{step.title}.</h2><p>{step.detail}</p><span className="shape-chip">{step.shape}</span></div>
        <div className="step-visual">
          {selected < 3 ? <div className={`explainer-image ${selected === 1 ? 'show-crop' : ''}`}><img src={selected === 2 ? analysis?.processed.preview || '/assets/reference-processed.png' : analysis?.imageUrl || '/samples/reference-tumor.jpg'} alt={selected === 2 ? 'Actual normalized reference input, shown as an RGB preview' : 'Reference MRI used to explain preprocessing'} />{selected === 1 ? <svg className="explainer-crop" viewBox={`0 0 ${sourceWidth} ${sourceHeight}`}><rect {...crop} fill="none" stroke="#b9eeeb" strokeWidth="1.5" strokeDasharray="5 4" vectorEffect="non-scaling-stroke" /></svg> : null}<span>{selected === 2 ? '240 × 240 / ACTUAL MODEL INPUT' : analysis ? 'CURRENT IMAGE' : 'SOURCE DATASET REFERENCE'}</span></div>
          : selected === 3 ? <div className="filter-visual"><div className="filter-stack">{Array.from({ length: 7 }, (_, i) => <div key={i} style={{ '--i': i } as React.CSSProperties} />)}</div><span className="mono">32 LEARNED FILTERS / SCHEMATIC</span></div>
          : <div className="decision-visual"><div className="decision-score">{analysis ? analysis.score.toFixed(4) : '0—1'}</div><span className="eyebrow">{analysis ? 'CURRENT TUMOR-CLASS SCORE' : 'SIGMOID OUTPUT RANGE'}</span><div className="decision-axis"><span>NO-TUMOR</span><i /><span>TUMOR</span></div><p>DECISION THRESHOLD = 0.5</p></div>}
        </div>
      </div>
    </section>
    <section className="network-section"><div className="section-heading"><div><span className="eyebrow">THE REFERENCE ARCHITECTURE</span><h2>Small network. Visible decisions.</h2></div><span className="mono muted">11,073 TRAINABLE · 64 NON-TRAINABLE</span></div><div className="network-flow">{[
      ['INPUT', '240² × 3', 'BGR pixels'], ['PAD + CONV', '238² × 32', '7 × 7 · 32 filters'], ['BN + RELU', '238² × 32', 'Normalize + activate'], ['POOL × 2', '14² × 32', '4 × 4 pooling'], ['DENSE', '6,272 → 1', 'Sigmoid output'],
    ].map(([title, shape, detail], i) => <div className="network-flow-item" key={title}><div className={`network-node node-${i}`}><Layers3 size={22} strokeWidth={1} /><strong>{title}</strong><span>{shape}</span><small>{detail}</small></div>{i < 4 ? <ArrowRight size={16} className="network-arrow" /> : null}</div>)}</div></section>
    <div className="learning-callout"><CircleHelp size={25} strokeWidth={1.3} /><div><h3>A useful question to ask.</h3><p>If a small change in crop, contrast or resolution changes the prediction, what does that tell us about the model? A convincing project investigates those failures.</p></div><button className="text-button" onClick={onWorkspace}>Try a reference <ArrowUpRight size={16} /></button></div>
  </div>;
}

import { Aperture, Check, Expand, Focus, ImagePlus, LoaderCircle, Minus, Plus, RotateCcw, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';
import type { Analysis, ImageView, Phase, SampleId } from '../lib/types';

interface Props {
  analysis?: Analysis;
  phase: Phase;
  filename: string;
  error?: string;
  busy: boolean;
  onFile: (file: File) => void;
  onSample: (id: SampleId) => void;
  onClear: () => void;
  onAttribution: () => void;
  imageView: ImageView;
  setImageView: (view: ImageView) => void;
  heatmap?: string;
  heatmapBusy: boolean;
  heatmapError?: string;
}

export default function ScanViewer(props: Props) {
  const { analysis, phase, busy, onFile, imageView, setImageView } = props;
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [contrast, setContrast] = useState(1);
  const [showCrop, setShowCrop] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  function pick() { if (!busy) input.current?.click(); }
  function fileChange(file?: File) { if (file) { setZoom(1); setContrast(1); onFile(file); } }
  const stageText: Record<string, string> = { loading: 'Loading the research engine', validating: 'Reading your image', preprocessing: 'Preparing the model input', inference: 'Running the neural network' };

  return <div className={`scan-panel panel ${dragging ? 'drag-active' : ''}`} ref={container}
    onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }}
    onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
    onDrop={event => { event.preventDefault(); setDragging(false); if (!busy) fileChange(event.dataTransfer.files[0]); }}>
    <input ref={input} type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" aria-label="Upload MRI image" className="file-input"
      onChange={event => { fileChange(event.target.files?.[0]); event.target.value = ''; }} />
    <div className="panel-header"><div className="panel-title"><span className="header-dot" /><span>SCAN VIEWER</span><span className="small-tag">2D IMAGE</span></div><div className="viewer-header-actions">
      {analysis ? <><button className="icon-button" onClick={pick} aria-label="Upload a new image" disabled={busy}><ImagePlus size={16} /></button><button className="icon-button" onClick={props.onClear} aria-label="Clear current image" disabled={busy}><X size={16} /></button></> : <span className="mono dim">DICOM NOT SUPPORTED</span>}
    </div></div>
    <div className="image-viewport">
      <div className="viewport-crosshair crosshair-h" /><div className="viewport-crosshair crosshair-v" />
      <span className="viewport-corner corner-tl" /><span className="viewport-corner corner-tr" /><span className="viewport-corner corner-bl" /><span className="viewport-corner corner-br" />
      {busy ? <div className="processing-view" role="status"><div className="processing-orbit"><Aperture size={42} /><span /></div><strong>{stageText[phase] || 'Preparing analysis'}</strong><span className="mono">{props.filename}</span><div className="processing-stages">{['validating', 'preprocessing', 'inference'].map((step, i) => <span key={step} className={['validating', 'preprocessing', 'inference'].indexOf(phase) >= i ? 'lit' : ''} />)}</div></div>
      : analysis ? <>
        <div className="scan-readout"><span>{analysis.sample ? 'REFERENCE IMAGE' : 'LOCAL IMAGE'}</span><span>{analysis.processed.quality.width} × {analysis.processed.quality.height} PX</span></div>
        <div className="scan-image-wrap" style={{ transform: `scale(${zoom})` }}>
          <img className="scan-image" src={imageView === 'original' ? analysis.imageUrl : analysis.processed.preview} alt={imageView === 'original' ? 'Original MRI input' : 'Cropped and resized model input'} style={{ filter: `contrast(${contrast})` }} />
          {imageView === 'attention' && props.heatmap ? <img className="heatmap-image" src={props.heatmap} alt="Computed Grad-CAM attribution overlay" /> : null}
          {imageView === 'original' && showCrop ? <svg className="crop-overlay" viewBox={`0 0 ${analysis.processed.quality.width} ${analysis.processed.quality.height}`}><rect {...analysis.processed.crop} fill="none" stroke="#b8edeb" strokeWidth="1.5" strokeDasharray="5 4" vectorEffect="non-scaling-stroke" /></svg> : null}
        </div>
        <div className="scan-bottom-readout"><span>{imageView === 'original' ? 'SOURCE / UNMODIFIED' : imageView === 'processed' ? 'MODEL INPUT / BGR · 240 × 240' : 'GRAD-CAM / PREDICTED CLASS'}</span><span>{Math.round(zoom * 100)}%</span></div>
        {props.heatmapBusy ? <div className="heatmap-loading" role="status"><LoaderCircle size={16} className="spin" /> Computing model attribution…</div> : null}
      </> : <div className="upload-zone">
        <button className="drop-target" onClick={pick} disabled={busy} aria-label="Choose an MRI image to analyze"><div className="upload-glyph"><Focus size={49} strokeWidth={0.8} /><Upload size={18} /></div><strong>{dragging ? 'Drop your image here' : 'Every scan starts a question.'}</strong><span>Drop an MRI image here, or <u>browse files</u></span><small>JPG / PNG · UP TO 20 MB · SINGLE IMAGE</small></button>
        {props.error ? <div className="input-error" role="alert"><span>INPUT NOT ANALYZED</span><p>{props.error}</p><button className="text-button" onClick={pick}>Choose another image <Upload size={14} /></button></div> : null}
        <div className="quick-references"><span>NO IMAGE HANDY?</span><button onClick={() => props.onSample('tumor')}>Try reference 01 ↗</button><button onClick={() => props.onSample('no-tumor')}>Try reference 02 ↗</button></div>
        <div className="upload-privacy"><Check size={13} /> Processed on this device. Never uploaded.</div>
      </div>}
    </div>
    <div className="viewer-toolbar">
      <div className="segmented-control" aria-label="Image display">
        <button aria-pressed={imageView === 'original'} disabled={!analysis || busy} onClick={() => setImageView('original')}>Original</button>
        <button aria-pressed={imageView === 'processed'} disabled={!analysis || busy} onClick={() => setImageView('processed')}>Model input</button>
        <button aria-pressed={imageView === 'attention'} disabled={!analysis || busy || props.heatmapBusy} onClick={props.onAttribution}>Attribution</button>
      </div>
      <div className="zoom-controls"><button className="icon-button" aria-label="Zoom out" disabled={!analysis || zoom <= 1} onClick={() => setZoom(v => Math.max(1, v - 0.25))}><Minus size={14} /></button><button className="icon-button" aria-label="Zoom in" disabled={!analysis || zoom >= 2.5} onClick={() => setZoom(v => Math.min(2.5, v + 0.25))}><Plus size={14} /></button><button className="icon-button" aria-label="Reset display" disabled={!analysis} onClick={() => { setZoom(1); setContrast(1); }}><RotateCcw size={13} /></button></div>
    </div>
    {analysis ? <div className="display-options"><label>Display contrast <input type="range" min="0.6" max="1.8" step="0.05" value={contrast} onChange={e => setContrast(Number(e.target.value))} /></label><button className={`text-button ${showCrop ? 'active' : ''}`} onClick={() => setShowCrop(v => !v)} aria-pressed={showCrop}><Expand size={13} /> Crop bounds</button></div> : null}
    {imageView === 'attention' ? <div className="attribution-caption">{props.heatmapError || <><div className="heatmap-legend"><span>LOWER INFLUENCE</span><i /><span>HIGHER INFLUENCE</span></div>Computed influence on the predicted class. Colors are scaled within this image. This is not a tumor outline.</>}</div> : null}
  </div>;
}

import { ArrowDownRight, ArrowUpRight, ScanLine } from 'lucide-react';

export default function Hero({ onExplore }: { onExplore: () => void }) {
  return <section className="hero" aria-labelledby="hero-title">
    <div className="hero-copy">
      <div className="eyebrow"><span className="tiny-cross">+</span> COMPUTATIONAL MRI RESEARCH <span className="edition">/ VOL. 01</span></div>
      <h1 id="hero-title">A closer look.<br /><span>A clearer question.</span></h1>
      <p>Explore what a neural network sees in a brain MRI.<br className="desktop-break" /> Follow the image. Question the prediction.</p>
      <div className="hero-actions"><a className="primary-button" href="#workspace"><ScanLine size={17} /> Explore a scan <ArrowDownRight size={17} /></a><button className="text-button" onClick={onExplore}>Inside the model <ArrowUpRight size={16} /></button></div>
      <div className="hero-footnote"><span className="status-dot" /> PRIVATE BY DESIGN <span className="footnote-divider" /> YOUR IMAGE STAYS IN YOUR BROWSER</div>
    </div>
    <div className="brain-scene" aria-label="Conceptual brain illustration">
      <div className="brain-grid" /><div className="brain-orbit orbit-one" /><div className="brain-orbit orbit-two" />
      <div className="brain-halo" />
      <img className="brain-art" src="/assets/brain-hero.png" alt="A luminous, anatomically inspired brain sculpture" fetchPriority="high" />
      <div className="brain-coordinate coordinate-top"><span>01 / NEURAL FIELD</span><i /></div>
      <div className="brain-coordinate coordinate-bottom"><i /><span>CONCEPTUAL VISUALIZATION</span></div>
      <div className="brain-axis"><span>Y</span><i /><span>X</span></div>
      <span className="brain-cross cross-one">+</span><span className="brain-cross cross-two">+</span>
    </div>
  </section>;
}

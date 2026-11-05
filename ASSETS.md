# Asset record

## Hero brain

- Tool: built-in `image_gen.imagegen` through the imagegen skill; no fallback CLI.
- Final saved project path: `public/assets/brain-hero.png`.
- Format: PNG with its generated transparency preserved; copied into the project without image editing.
- Role: conceptual editorial illustration. It is not used for inference or presented as a real MRI.

Final prompt:

> Use case: stylized-concept. Asset type: centerpiece for an exceptionally refined MRI research web application, used on a near-black navy canvas. Create a single highly detailed three-dimensional human brain sculpture, floating isolated on a genuinely transparent background. Three-quarter front view, cerebral hemispheres, complex anatomically inspired gyri, subtle cerebellum and short brainstem visible. Material: smoked translucent charcoal glass with silver-white and pale icy cyan luminous fine contour lines and intricate filament-like neural lattice tracing the entire surface, fine scattered luminous points. A small restrained warm coral rim light along a few lower folds. Museum-quality scientific sculpture meets premium computational design; crisp, very detailed, photographic 3D render with true dimensional depth and controlled subtle bloom. Brain fills approximately 85 percent of a square canvas, centered, fully contained. No text, labels, grids, framing, halo circle, pedestal, diagram, MRI scan, medical annotations, tumor, logos, watermarks, extra objects or background. The brain is a conceptual editorial visualization, not a medical scan.

## Reference and processed images

- `public/samples/reference-tumor.jpg` — pinned upstream `yes/Y1.jpg`; SHA-256 `27a43972bf6b6bb00fd071791c3925f422295c16f881ef8c395a9534f12cf0af`.
- `public/samples/reference-no-tumor.jpeg` — pinned upstream `no/1 no.jpeg`; SHA-256 `e4d9d83f89339366f4f77137d440a4c3b62e799a482ebfa6c79c9209d47ffdc9`.
- `public/assets/reference-processed.png` — actual OpenCV crop and cubic resize of reference 01, used to explain preprocessing when no active image is selected.

These are source-dataset examples. See `THIRD-PARTY-NOTICES.md` for attribution and rights metadata. Neither is labelled as an independently held-out example.

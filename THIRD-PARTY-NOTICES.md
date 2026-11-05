# Credits and source notices

## Reference network

Original project: **MohamedAliHabib/Brain-Tumor-Detection**, by Mohamed Ali Habib.

Pinned source: https://github.com/MohamedAliHabib/Brain-Tumor-Detection/tree/30470ae8eb2e4a523df7dc45dd5323903cb98365

The original model/code is distributed under Apache License 2.0. The full source license is retained at `public/models/care-baseline/LICENSE.txt` and in the built app at `/models/care-baseline/LICENSE.txt`. This rebuild preserves the selected checkpoint's numerical weights and credits its origin. It adds a new interface, a browser representation of those arrays, quality checks, attribution, offline support and a research workflow.

## MRI reference images

The two reference examples correspond to `yes/Y1.jpg` and `no/1 no.jpeg` in the pinned source repository. They are used as credited educational source examples, not independent test cases. The original project links to Navoneel Chakrabarty's [Brain MRI Images for Brain Tumor Detection](https://www.kaggle.com/datasets/navoneel/brain-mri-images-for-brain-tumor-detection) dataset. Kaggle's public metadata identifies the data-file rights as **Data files © Original Authors**. The model/code license is not presented as a separate verification of the underlying images' rights or patient provenance.

## Runtime and presentation libraries

- React / React DOM — MIT.
- TensorFlow.js — Apache 2.0.
- OpenCV.js, supplied by `@techstark/opencv-js` — Apache 2.0; the pinned build is self-hosted.
- Lucide icons — ISC.
- Manrope and IBM Plex Mono fonts — SIL Open Font License.
- Vite, TypeScript and esbuild are development/build tools; their installed packages retain their notices.

## Artwork

The hero brain is generated editorial artwork, not a patient image, model output or anatomically validated medical rendering. It is labelled conceptual visualization in the app. See `ASSETS.md` for its final prompt and saved path.

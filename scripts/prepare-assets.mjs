import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
mkdirSync('public/vendor', { recursive: true });
copyFileSync('node_modules/@techstark/opencv-js/dist/opencv.js', 'public/vendor/opencv.js');
mkdirSync('public/licenses', { recursive: true });
for (const [name, pkg] of [['React','react'], ['React-DOM','react-dom'], ['OpenCV-js','@techstark/opencv-js'], ['Lucide','lucide-react'], ['Manrope','@fontsource-variable/manrope'], ['IBM-Plex-Mono','@fontsource/ibm-plex-mono']]) {
  copyFileSync(`node_modules/${pkg}/LICENSE`, `public/licenses/${name}.txt`);
}
writeFileSync('public/licenses/TensorFlow-js.txt', 'TensorFlow.js — Copyright 2024 Google LLC. All Rights Reserved.\n\n' + readFileSync('public/models/care-baseline/LICENSE.txt', 'utf8'));
console.log('Prepared self-hosted OpenCV runtime and dependency license texts.');

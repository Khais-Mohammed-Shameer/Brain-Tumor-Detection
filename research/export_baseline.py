"""Export audited HDF5 arrays and parity fixtures. Does not retrain the model."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import cv2
import h5py
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=ROOT/'assessment/received/models/cnn-parameters-improvement-23-0.91.model')
args = parser.parse_args()
expected = 'e14c6af5b389c603242b171db841c407b6bfe65150b0d32dbd6590ec4d178e8f'
assert hashlib.sha256(args.source.read_bytes()).hexdigest() == expected, 'Unexpected source model; verify provenance before exporting.'
specs = [('conv_kernel','conv0/conv0/kernel:0'),('conv_bias','conv0/conv0/bias:0'),
         ('bn_gamma','bn0/bn0/gamma:0'),('bn_beta','bn0/bn0/beta:0'),
         ('bn_mean','bn0/bn0/moving_mean:0'),('bn_variance','bn0/bn0/moving_variance:0'),
         ('dense_kernel','fc/fc/kernel:0'),('dense_bias','fc/fc/bias:0')]
out = ROOT/'public/models/care-baseline'
out.mkdir(parents=True, exist_ok=True)
arrays=[]
manifest={'id':'care-reference-cnn-v1','format':'care-arrays-v1','parameters':11137,
          'input':[240,240,3],'output':'sigmoid tumor-class score','threshold':0.5,
          'source':{'author':'Mohamed Ali Habib','repository':'https://github.com/MohamedAliHabib/Brain-Tumor-Detection',
                    'commit':'30470ae8eb2e4a523df7dc45dd5323903cb98365','checkpoint':args.source.name,'sha256':expected,
                    'license':'Apache-2.0'},'tensors':[]}
with h5py.File(args.source) as f:
    for name,key in specs:
        a=np.asarray(f['model_weights/'+key][:], dtype='<f4')
        arrays.append(a.tobytes())
        manifest['tensors'].append({'name':name,'shape':list(a.shape),'length':a.size})
data=b''.join(arrays)
manifest['weights_sha256']=hashlib.sha256(data).hexdigest()
(out/'weights.bin').write_bytes(data)
(out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
audit=ROOT/'assessment'
shutil.copy2(audit/'upstream/LICENSE',out/'LICENSE.txt')
shutil.copy2(audit/'audit-fixtures/upstream_tumor_label.jpg',ROOT/'public/samples/reference-tumor.jpg')
shutil.copy2(audit/'audit-fixtures/upstream_no_tumor_label.jpeg',ROOT/'public/samples/reference-no-tumor.jpeg')

# Expected tensors come from the original BGR/cubic OpenCV pipeline, not the old wrapper.
parity=[]
for name in ['reference-tumor.jpg','reference-no-tumor.jpeg']:
    path=ROOT/'public/samples'/name
    image=cv2.imread(str(path))
    gray=cv2.GaussianBlur(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),(5,5),0)
    mask=cv2.threshold(gray,45,255,cv2.THRESH_BINARY)[1]
    mask=cv2.dilate(cv2.erode(mask,None,iterations=2),None,iterations=2)
    contours=cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
    c=max(contours,key=cv2.contourArea)
    l=int(c[c[:,:,0].argmin()][0][0]);r=int(c[c[:,:,0].argmax()][0][0])
    t=int(c[c[:,:,1].argmin()][0][1]);b=int(c[c[:,:,1].argmax()][0][1])
    resized=cv2.resize(image[t:b,l:r],(240,240),interpolation=cv2.INTER_CUBIC)
    tensor=(resized/255).astype('<f4')
    target=ROOT/'tests'/(Path(name).stem+'.f32')
    target.write_bytes(tensor.tobytes())
    parity.append({'file':name,'crop':{'x':l,'y':t,'width':r-l,'height':b-t},
                   'tensor':target.name,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'tests/parity-fixtures.json').write_text(json.dumps(parity,indent=2)+'\n')
print('Exported audited baseline:',len(data),'bytes;',len(manifest['tensors']),'tensors.')

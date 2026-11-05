"""Reproducible local research workflow. No data is downloaded or uploaded.

Input CSV: path,label,group. Labels are 0/1; group is a verified patient ID,
or an original-image family ID when patient IDs are unavailable. Augmented
copies must share a group. The person preparing the data owns that assertion.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
import cv2
import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    path = Path(path).resolve()
    with path.open(newline='') as file:
        rows = list(csv.DictReader(file))
    if not rows or not {'path', 'label', 'group'}.issubset(rows[0]):
        raise ValueError('CSV needs path,label,group columns and at least one row.')
    seen_paths = set()
    for row in rows:
        row['path'] = str((path.parent / row['path']).resolve())
        if row['path'] in seen_paths:
            raise ValueError('The same path appears more than once in the manifest.')
        seen_paths.add(row['path'])
        if row['label'] not in ['0', '1'] or not row['group'].strip():
            raise ValueError('Labels must be 0 or 1 and every image needs a nonempty group.')
        actual = digest(row['path'])
        if row.get('sha256') and row['sha256'] != actual:
            raise ValueError(f'Image changed since the split was frozen: {row["path"]}')
        row['sha256'] = actual
    return rows


def grouped_split(rows, seed=42):
    """Keep supplied groups intact and reject duplicate content across groups."""
    hashes = {}
    for row in rows:
        prior = hashes.setdefault(row['sha256'], row)
        if prior['label'] != row['label']:
            raise ValueError('Identical image bytes have conflicting labels.')
        if prior['group'] != row['group']:
            raise ValueError('Identical image bytes have different group IDs. Correct the grouping before splitting.')
    groups = sorted({row['group'] for row in rows})
    if len(groups) < 10:
        raise ValueError('At least 10 independent groups are required for a three-way split.')
    rng = random.Random(seed)
    ntest = max(2, round(len(groups) * .15))
    nval = max(2, round(len(groups) * .15))
    best = None
    for _ in range(500):
        shuffled = groups.copy(); rng.shuffle(shuffled)
        assignment = {g: 'test' if i < ntest else 'validation' if i < ntest+nval else 'train' for i,g in enumerate(shuffled)}
        counts = {split: [0, 0] for split in ['train','validation','test']}
        for row in rows: counts[assignment[row['group']]][int(row['label'])] += 1
        if any(min(values) == 0 for values in counts.values()): continue
        positive_rate = sum(int(row['label']) for row in rows) / len(rows)
        penalty = sum(abs(values[1]/sum(values)-positive_rate) for values in counts.values())
        if best is None or penalty < best[0]: best = penalty, assignment, counts
    if best is None:
        raise ValueError('Could not create three independent subsets containing both labels. Supply more groups.')
    return [{**row, 'split': best[1][row['group']]} for row in rows], best[2]


def assert_independent(rows):
    groups, hashes = {}, {}
    for row in rows:
        if row.get('split') not in ['train', 'validation', 'test']:
            raise ValueError('Every row must have a train, validation or test split.')
        for index, key in [(groups, row['group']), (hashes, row['sha256'])]:
            if index.setdefault(key, row['split']) != row['split']:
                raise ValueError('Group or duplicate-image leakage detected across splits.')


def image_input(path):
    image = cv2.imread(str(path))
    if image is None: raise ValueError(f'Unreadable image: {path}')
    if min(image.shape[:2]) < 64: raise ValueError(f'Image is smaller than 64 pixels: {path}')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    step = max(1, int(np.ceil(np.sqrt(gray.size/250000))))
    a = gray[:-1:step, :-1:step].astype(float)
    std = a.std()
    variation = (np.abs(a-gray[:-1:step,1::step]) + np.abs(a-gray[1::step,:-1:step])) / 2
    if std < 7 or variation.mean()/max(std,1) > .95:
        raise ValueError(f'Blank/low-contrast or high-frequency noise input: {path}')
    blurred = cv2.GaussianBlur(gray,(5,5),0)
    mask = cv2.threshold(blurred,45,255,cv2.THRESH_BINARY)[1]
    mask = cv2.dilate(cv2.erode(mask,None,iterations=2),None,iterations=2)
    contours = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
    if not contours: raise ValueError(f'No usable foreground: {path}')
    c = max(contours,key=cv2.contourArea)
    x,y,w,h = cv2.boundingRect(c); w-=1;h-=1
    if min(w,h)<20 or cv2.contourArea(c)/gray.size<.02:
        raise ValueError(f'Foreground is too small: {path}')
    return (cv2.resize(image[y:y+h,x:x+w],(240,240),interpolation=cv2.INTER_CUBIC)/255).astype(np.float32)


def metrics(labels, scores):
    y = np.asarray(labels, dtype=int); scores=np.asarray(scores,dtype=float)
    if y.size == 0 or y.shape != scores.shape or not np.isin(y,[0,1]).all() or not np.isfinite(scores).all() or ((scores<0)|(scores>1)).any():
        raise ValueError('Need equally sized nonempty 0/1 labels and finite 0–1 scores.')
    p = scores > .5
    tp=int(((y==1)&p).sum());tn=int(((y==0)&~p).sum())
    fp=int(((y==0)&p).sum());fn=int(((y==1)&~p).sum())
    def ratio(a,b): return a/b if b else None
    positive=scores[y==1];negative=scores[y==0]
    # Mann-Whitney interpretation of AUROC, with half credit for ties.
    auc=float(((positive[:,None]>negative).sum()+.5*(positive[:,None]==negative).sum())/(len(positive)*len(negative))) if len(positive) and len(negative) else None
    return {'n':int(y.size),'confusion_matrix':{'tn':tn,'fp':fp,'fn':fn,'tp':tp},
            'accuracy':ratio(tp+tn,len(y)),'sensitivity':ratio(tp,tp+fn),'specificity':ratio(tn,tn+fp),
            'precision':ratio(tp,tp+fp),'f1':ratio(2*tp,2*tp+fp+fn),'auroc':auc,'threshold':.5}


def make_core(tf):
    inputs=tf.keras.Input((240,240,3))
    x=tf.keras.layers.ZeroPadding2D(2)(inputs)
    x=tf.keras.layers.Conv2D(32,7,name='conv0')(x)
    x=tf.keras.layers.BatchNormalization(axis=3,name='bn0')(x)
    x=tf.keras.layers.Activation('relu')(x)
    x=tf.keras.layers.MaxPooling2D(4)(x)
    x=tf.keras.layers.MaxPooling2D(4)(x)
    x=tf.keras.layers.Flatten()(x)
    x=tf.keras.layers.Dropout(.3)(x)
    output=tf.keras.layers.Dense(1,activation='sigmoid',name='fc')(x)
    return tf.keras.Model(inputs,output,name='care_fresh_cnn')


def train(args):
    import tensorflow as tf
    rows=read_rows(args.manifest);assert_independent(rows)
    if args.output.exists(): raise ValueError('Output already exists. Use a new run directory to preserve prior evidence.')
    subsets={split:[r for r in rows if r['split']==split] for split in ['train','validation','test']}
    if any({r['label'] for r in subset}!={'0','1'} for subset in subsets.values()):
        raise ValueError('Every split must contain both labels.')
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()
    # The test set is not decoded, fitted, scored or used for model selection here.
    def arrays(subset): return np.stack([image_input(r['path']) for r in subset]),np.array([int(r['label']) for r in subset],dtype=np.float32)
    xtrain,ytrain=arrays(subsets['train']);xval,yval=arrays(subsets['validation'])
    core=make_core(tf)
    augmentation=tf.keras.Sequential([tf.keras.layers.RandomFlip('horizontal',seed=args.seed),tf.keras.layers.RandomRotation(.03,seed=args.seed+1),tf.keras.layers.RandomTranslation(.04,.04,seed=args.seed+2)])
    inputs=tf.keras.Input((240,240,3));model=tf.keras.Model(inputs,core(augmentation(inputs)))
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),loss='binary_crossentropy',metrics=['accuracy'])
    history=model.fit(xtrain,ytrain,validation_data=(xval,yval),batch_size=16,epochs=args.epochs,
                      callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=6,restore_best_weights=True)],verbose=2)
    args.output.mkdir(parents=True)
    core.save(args.output/'model.keras')
    metadata={'seed':args.seed,'tensorflow':tf.__version__,'manifest_sha256':digest(args.manifest),
              'train_groups':sorted({r['group'] for r in subsets['train']}),'validation_groups':sorted({r['group'] for r in subsets['validation']}),
              'train_validation_image_hashes':sorted({r['sha256'] for r in subsets['train']+subsets['validation']}),
              'model_sha256':digest(args.output/'model.keras'),'test_evaluated':False,
              'preprocessing':'BGR/cubic/240x240/divide255; browser-compatible basic quality checks',
              'history':{key:[float(v) for v in values] for key,values in history.history.items()}}
    (args.output/'training.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Training complete. Test set remains untouched. Run evaluate once after finalizing choices.')


def evaluate(args):
    import tensorflow as tf
    rows=read_rows(args.manifest);assert_independent(rows)
    run=Path(args.run);metadata=json.loads((run/'training.json').read_text())
    if metadata['manifest_sha256']!=digest(args.manifest) or metadata['model_sha256']!=digest(run/'model.keras'):
        raise ValueError('Model or frozen manifest differs from the training record.')
    if (run/'test-results.json').exists(): raise ValueError('Final test results already exist. Preserve them; do not repeatedly tune against the test set.')
    test=[r for r in rows if r['split']=='test']
    seen_groups=set(metadata['train_groups']+metadata['validation_groups'])
    seen_hashes=set(metadata['train_validation_image_hashes'])
    if any(r['group'] in seen_groups or r['sha256'] in seen_hashes for r in test): raise ValueError('Test leakage detected.')
    model=tf.keras.models.load_model(run/'model.keras',compile=False,safe_mode=True)
    scores=model.predict(np.stack([image_input(r['path']) for r in test]),verbose=0).reshape(-1)
    labels=np.array([int(r['label']) for r in test]);summary=metrics(labels,scores)
    # Resample groups, keeping all images from each selected group together.
    groups=sorted({r['group'] for r in test});rng=np.random.default_rng(42);replicates=[]
    indices={g:[i for i,r in enumerate(test) if r['group']==g] for g in groups}
    for _ in range(1000):
        selected=np.concatenate([indices[g] for g in rng.choice(groups,len(groups),replace=True)])
        replicates.append(metrics(labels[selected],scores[selected]))
    intervals={}
    for key in ['accuracy','sensitivity','specificity','precision','f1','auroc']:
        values=[r[key] for r in replicates if r[key] is not None]
        intervals[key]=[float(v) for v in np.quantile(values,[.025,.975])] if values else None
    summary.update({'group_bootstrap_95_percentile_intervals':intervals,'independent_test_groups':len(groups),
                    'manifest_sha256':digest(args.manifest),'model_sha256':digest(run/'model.keras'),
                    'limitation':'Independence is only as reliable as the supplied group IDs. Image-family grouping is not proof of patient independence.',
                    'predictions':[{'sha256':r['sha256'],'group':r['group'],'label':int(r['label']),'score':float(s)} for r,s in zip(test,scores)]})
    (run/'test-results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='predictions'},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    split=sub.add_parser('split');split.add_argument('input',type=Path);split.add_argument('output',type=Path);split.add_argument('--seed',type=int,default=42);split.add_argument('--grouping',choices=['patient','original-image'],required=True)
    training=sub.add_parser('train');training.add_argument('manifest',type=Path);training.add_argument('output',type=Path);training.add_argument('--seed',type=int,default=42);training.add_argument('--epochs',type=int,default=30)
    evaluation=sub.add_parser('evaluate');evaluation.add_argument('manifest',type=Path);evaluation.add_argument('run',type=Path)
    args=parser.parse_args()
    if args.command=='split':
        if args.output.exists(): raise ValueError('Split output already exists; preserve the frozen split or choose a new path.')
        rows,counts=grouped_split(read_rows(args.input),args.seed);assert_independent(rows)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=['path','label','group','sha256','split'],extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        args.output.with_suffix('.json').write_text(json.dumps({'seed':args.seed,'grouping_asserted_by_preparer':args.grouping,'counts_0_1':counts,'manifest_sha256':digest(args.output),'note':'Review near-duplicates and provenance before training. Group IDs are not verified by this tool.'},indent=2)+'\n')
        print(json.dumps(counts,indent=2))
    elif args.command=='train':train(args)
    else:evaluate(args)


if __name__=='__main__':main()

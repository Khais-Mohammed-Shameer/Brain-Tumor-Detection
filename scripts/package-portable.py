"""Package the production app without source, dependencies or research data."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
out=root/'outputs/C.A.R.E.-Science-Fair.zip'
out.parent.mkdir(exist_ok=True)
if not (root/'dist/sw.js').is_file():raise SystemExit('Run npm run build first.')
start='''C.A.R.E. — MRI Research Studio

1. Extract this entire ZIP to a folder.
2. Install Python 3 if it is not already on the demonstration computer.
3. Windows: double-click Start C.A.R.E.bat.
   macOS: run python3 serve.py in Terminal from the extracted folder.
   Linux: run python3 serve.py from the extracted folder.
4. Your browser opens http://127.0.0.1:8765/.

No Python packages, TensorFlow installation, account or Internet connection
are needed to run this extracted build. Keep its terminal window open.
If the port is occupied, run python3 serve.py --port 8766.

Try reference 01 or 02, inspect Model input, then compute Attribution.
Use Evidence and Inside the model to explain the experiment.

The shipped neural-network weights are a credited reference model, not
a newly trained or clinically validated diagnostic system. The two MRI
examples are source-dataset references, not independent test cases.

See DEMO-GUIDE.md and THIRD-PARTY-NOTICES.md for details and credits.
'''
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('C.A.R.E.-Studio/START-HERE.txt',start)
    for name in ['serve.py','Start C.A.R.E.command','Start C.A.R.E.bat','DEMO-GUIDE.md','THIRD-PARTY-NOTICES.md']:
        z.write(root/name,'C.A.R.E.-Studio/'+name)
    for path in sorted((root/'dist').rglob('*')):
        if path.is_file():z.write(path,'C.A.R.E.-Studio/'+str(path.relative_to(root)))
print(out)
print(f'{out.stat().st_size/1024/1024:.2f} MB; includes the complete built app and local launcher.')

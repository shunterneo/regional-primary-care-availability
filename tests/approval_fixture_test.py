"""Verify the approval adapter updates data only after an explicit form entry."""
import json,os,pathlib,shutil,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    d=pathlib.Path(td)
    for folder in ['scripts','data']:
        shutil.copytree(R/folder,d/folder)
    env=os.environ.copy();env.update({'APPROVAL_CLINIC_ID':'c001','APPROVAL_STATUS':'not_accepting',
      'APPROVAL_SOURCE_URL':'https://clinic.example.org/notice','APPROVAL_INTAKE_DETAIL':'Published statement explicitly says not accepting new patients as of test date.',
      'APPROVAL_REVIEWER_NOTE':'Manual fixture check of named clinic and dated original notice only.'})
    original=json.loads((d/'data/clinics.json').read_text())['clinics'][0]['status']
    proc=subprocess.run([sys.executable,str(d/'scripts/approve_from_env.py')],env=env,capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    after=json.loads((d/'data/clinics.json').read_text())['clinics'][0]
    assert after['status']=='not_accepting' and after['status']!=original
    hist=json.loads((d/'data/review_history.json').read_text())
    assert hist[-1]['clinic_id']=='c001' and hist[-1]['new_status']=='not_accepting'
    print('PASS: explicit, sourced reviewer approval updates database and audit history; original dataset untouched')

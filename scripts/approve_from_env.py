#!/usr/bin/env python3
"""Apply a GitHub Actions manual approval form without shell-interpolated inputs."""
from __future__ import annotations
import os,subprocess,sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
args=[]
for cli,env in [('id','APPROVAL_CLINIC_ID'),('status','APPROVAL_STATUS'),('source','APPROVAL_SOURCE_URL'),('detail','APPROVAL_INTAKE_DETAIL'),('reviewer-note','APPROVAL_REVIEWER_NOTE')]:
    val=os.getenv(env,'').strip()
    if not val:raise SystemExit(f'Missing {env}')
    if len(val)>1000:raise SystemExit(f'{env} too long')
    args.extend(['--'+cli,val])
subprocess.run([sys.executable,str(ROOT/'scripts'/'update_status.py'),*args],check=True,cwd=ROOT)

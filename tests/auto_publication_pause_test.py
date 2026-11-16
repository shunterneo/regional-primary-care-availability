#!/usr/bin/env python3
"""Offline containment: default/invalid switches never read or write live data."""
import contextlib, datetime as dt, io, json, os, pathlib, sys, tempfile
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import auto_publish
from auto_evidence import decisive_statement, observe, scope_identity, scope_fingerprint

today = dt.date.today()
day = today.isoformat()
url = 'https://example.test/intake'
quote = 'Our family practice is now accepting new patients.'
database = {'clinics': [{'id': 'fixture', 'name': 'Synthetic clinic', 'status': 'unknown',
    'clinic_url': 'https://example.test/', 'evidence_url': url, 'care_model': 'ongoing',
    'last_reviewed': (today-dt.timedelta(days=2)).isoformat()}], 'data_as_of': day}
clinic=database['clinics'][0]
clinic['auto_publication_scope']={'version':1,'clinic_id':clinic['id'],'source_url':url,'scope':'single_office',
    'reviewed_on':day,'method':'independent_public_source_review','evidence':'Synthetic reviewed single-office source.',
    'identity_hash':scope_identity(clinic),'context_template_hash':decisive_statement(quote)['template_hash']}
observation = observe({}, decisive_statement(quote), (today-dt.timedelta(days=1)).isoformat()+'T13:00:00+00:00',scope_hash=scope_fingerprint(clinic))
observation = observe(observation, decisive_statement(quote), day+'T13:00:00+00:00',scope_hash=scope_fingerprint(clinic))
source = {'sources': {url: {'official_first_party': True, 'last_error': None, 'auto_observation': observation,
    'last_success':observation['last_seen'],'final_url':url}}}

with tempfile.TemporaryDirectory() as folder:
    root = pathlib.Path(folder)
    paths = {'DB': root/'clinics.json', 'SRC': root/'source_state.json', 'HISTORY': root/'history.json'}
    paths['DB'].write_text(json.dumps(database)); paths['SRC'].write_text(json.dumps(source)); paths['HISTORY'].write_text('[]')
    before = {name: path.read_bytes() for name,path in paths.items()}
    with patch.multiple(auto_publish, **paths):
        for value in (None, '', 'false', 'False', 'TRUE', '1', ' true', 'true '):
            with patch.dict(os.environ):
                if value is None: os.environ.pop('AUTO_PUBLICATION_ENABLED', None)
                else: os.environ['AUTO_PUBLICATION_ENABLED'] = value
                output = io.StringIO()
                with contextlib.redirect_stdout(output): assert auto_publish.run() == 0
                assert 'PAUSED' in output.getvalue()
                assert all(path.read_bytes()==before[name] for name,path in paths.items()), value
        # The pause guards before file reads, not only before writes.
        with patch.dict(os.environ, {'AUTO_PUBLICATION_ENABLED': 'false'}), patch.object(auto_publish, 'DB', root/'missing.json'):
            with contextlib.redirect_stdout(io.StringIO()): assert auto_publish.run() == 0
        # Explicit reversibility is exercised ONLY against synthetic temp files.
        with patch.dict(os.environ, {'AUTO_PUBLICATION_ENABLED': 'true'}):
            with contextlib.redirect_stdout(io.StringIO()): assert auto_publish.run() == 0
        assert json.loads(paths['DB'].read_text())['clinics'][0]['status']=='accepting'
        assert len(json.loads(paths['HISTORY'].read_text()))==1
        assert paths['SRC'].read_bytes()==before['SRC']

workflow=(pathlib.Path(__file__).resolve().parents[1]/'.github/workflows/daily-site.yml').read_text()
assert "AUTO_PUBLICATION_ENABLED: 'false'" in workflow
for command in ('check_sources.py','discover_clinics.py','directory_discovery.py','registry_audit.py','review_notices.py'):
    assert 'python scripts/'+command in workflow
print('PASS: paused by default; invalid values fail closed; records/history/observations unchanged; scanning/review retained; explicit switch reversible in isolated fixture')

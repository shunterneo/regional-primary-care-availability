"""Recovery workflow may persist observations, never clinic or profile facts."""
import pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=(ROOT/'.github/workflows/source-recovery.yml').read_text()
assert "AUTO_PUBLICATION_ENABLED: 'false'" in s
for forbidden in ['python scripts/auto_publish.py','python scripts/official_registry.py','python scripts/update_status.py','python scripts/apply_site_edit.py','python scripts/ai_triage.py','gh issue','gh pr']:
 assert forbidden not in s,forbidden
assert 'python scripts/check_sources.py' in s and 'python scripts/directory_discovery.py' in s
add=re.findall(r'^\s*git add (.+)$',s,re.M)
assert len(add)==1
assert set(add[0].split())=={'data/source_state.json','data/review_queue.json','data/directory_state.json','data/directory_queue.json'}
assert 'git diff --exit-code -- data/clinics.json data/review_history.json data/extra_communities.json data/official_registry_state.json' in s
assert s.index('Mark incomplete recovery visibly')>s.index('Preserve scan evidence')>s.index('Save scan state')
assert 'run: python scripts/monitor_health.py' in s
print('PASS: recovery is explicitly paused, checks source+directory, saves observation-only whitelist, preserves evidence before visible unhealthy exit, no outreach')

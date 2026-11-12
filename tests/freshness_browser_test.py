import os
"""Browser regression for static-site expiry, and a real CSV download."""
import pathlib,datetime,json
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.clock.install(time=datetime.datetime(2027,1,1,tzinfo=datetime.timezone.utc))
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((root/'site/index.html').as_uri())
    assert page.locator('#mIntake').inner_text()=='0','Old static build must not advertise expired openings'
    page.select_option('#status','accepting')
    assert page.locator('#results .item').count()==0
    page.select_option('#status','needs_review')
    assert page.locator('#results .item').count()>0
    page.click('#downloadOpen')
    page.select_option('#downloadScope','all')
    page.select_option('#downloadFormat','csv')
    with page.expect_download() as download:
        page.click('#downloadGo')
    text=pathlib.Path(download.value.path()).read_text()
    assert 'Needs reconfirmation' in text
    assert 'Applications advertised' not in text
    assert not errors,errors
    browser.close()
print('PASS: real browser removes expired advertised openings without server rebuild')

"""Verify published Seans without mocks, recording actual host responses."""
import json, pathlib, os, traceback
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent/'public-test-results'; OUT.mkdir(exist_ok=True)
URL = os.environ.get('SEANS_PUBLIC_URL','https://raw.githack.com/KADARstudio/WycenaSesji/seans-v02-release/film-duel/index.html')
rows=[]
with sync_playwright() as p:
    for engine in ['chromium','webkit']:
        b=getattr(p,engine).launch()
        c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='pl-PL',timezone_id='Europe/Warsaw')
        page=c.new_page(); row={'engine':engine,'passed':False,'errors':[],'failedResponses':[]};rows.append(row)
        page.on('pageerror',lambda e,r=row:r['errors'].append(str(e)))
        page.on('response',lambda response,r=row:r['failedResponses'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
        try:
            response=page.goto(URL,wait_until='domcontentloaded',timeout=45000)
            row['initialStatus']=response.status
            page.wait_for_timeout(1500)
            row['initialTitle']=page.title();row['initialText']=page.locator('body').inner_text()[:12000]
            (OUT/f'{engine}-initial.html').write_text(page.content())
            page.screenshot(path=str(OUT/f'{engine}-initial.png'),full_page=True)
            if page.title().startswith('External Content Notice'):
                # Ordinary visible hosting confirmation, only for our exact app.
                assert page.locator('#phish-dest').input_value()==URL
                page.get_by_role('button',name='Open the page',exact=True).click()
                row['hostingNoticeAccepted']=True
            page.wait_for_function("window.SeansV02?.version==='0.2.0'",timeout=30000)
            page.wait_for_selector('[data-service="netflix"]',timeout=35000)
            page.locator('[data-service="netflix"]').click();page.locator('[data-action="start"]').click()
            page.locator('.pick').first.click();page.wait_for_function('!SeansV02.busy')
            assert page.evaluate('SeansV02.snapshot().game.completed===1')
            page.screenshot(path=str(OUT/f'{engine}-duel.png'),full_page=True)
            page.locator('[data-action="finish"]').click();page.wait_for_function('!SeansV02.busy')
            assert page.locator('.session-stats').count()==1
            page.screenshot(path=str(OUT/f'{engine}-winner.png'),full_page=True)
            row['version']=page.evaluate('SeansV02.version');row['catalogueMovies']=page.evaluate('catalogue.movies.length')
            row['catalogueFetchedAt']=page.evaluate('catalogue.fetchedAt');row['passed']=not row['errors']
        except Exception as e:
            row['error']=str(e);row['traceback']=traceback.format_exc()
            row['finalUrl']=page.url;row['finalTitle']=page.title();row['finalText']=page.locator('body').inner_text()[:12000]
            page.screenshot(path=str(OUT/f'{engine}-failure.png'),full_page=True)
        finally:b.close()
report={'url':URL,'commit':os.environ.get('GITHUB_SHA'),'results':rows}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if not all(r['passed'] for r in rows):raise SystemExit(1)

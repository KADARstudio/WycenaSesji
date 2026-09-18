"""Live-network browser smoke tests for the private Seans prototype."""
import functools, http.server, json, pathlib, threading, urllib.request
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
public_url='https://raw.githack.com/KADARstudio/WycenaSesji/film-duel-prototype/film-duel/index.html'
report=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch()
  context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True,locale='pl-PL',timezone_id='Europe/Warsaw')
  page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.goto(url);page.locator('[data-service="netflix"]').wait_for(timeout=35000)
  assert page.locator('[data-action="start"]').is_disabled()
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  page.locator('[data-service="netflix"]').click();page.locator('[data-service="prime"]').click()
  assert page.locator('[data-action="start"]').is_enabled()
  page.locator('[data-rounds="10"]').click()
  page.screenshot(path=str(OUT/f'{engine}-home.png'),full_page=True)
  page.locator('[data-action="start"]').click()
  first=page.locator('[data-movie]').evaluate_all('(els)=>els.map(e=>e.dataset.movie)')
  page.locator('.pick[data-pick="1"]').click()
  second=page.locator('[data-movie]').evaluate_all('(els)=>els.map(e=>e.dataset.movie)')
  assert second[1]==first[1] and second[0] not in first
  assert page.locator('.badge.champ').count()==1
  page.locator('[data-action="undo"]').click()
  assert page.locator('[data-movie]').evaluate_all('(els)=>els.map(e=>e.dataset.movie)')==first
  page.locator('[data-seen="0"]').click()
  assert page.locator('[data-movie]').first.get_attribute('data-movie') not in first
  page.locator('[data-action="undo"]').click()
  assert page.locator('[data-movie]').evaluate_all('(els)=>els.map(e=>e.dataset.movie)')==first
  page.locator('[data-detail]').first.click();assert page.locator('dialog').is_visible();page.locator('[data-action="close"]').click()
  page.locator('.pick[data-pick="0"]').click()
  page.wait_for_function('Array.from(document.querySelectorAll(".duel img.poster")).length===2 && Array.from(document.querySelectorAll(".duel img.poster")).every(i=>i.complete&&i.naturalWidth>0)',timeout=20000)
  page.wait_for_timeout(350)
  page.screenshot(path=str(OUT/f'{engine}-duel.png'),full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  for i in range(9):
   page.locator('.pick[data-pick="0"]').click();page.wait_for_timeout(270)
  page.locator('.winner').wait_for();assert page.locator('.winner-intro').inner_text().startswith('10 ')
  links=page.locator('.watch-links a').evaluate_all('(els)=>els.map(e=>e.href)');assert links and all(u.startswith('https://') for u in links)
  page.screenshot(path=str(OUT/f'{engine}-winner.png'),full_page=True)
  page.locator('[data-action="save"]').click();page.locator('[data-action="library"]').click();assert page.locator('.library-row').count()==1
  page.locator('.library [data-action="home"]').click()
  page.reload();page.locator('[data-action="resume"]').wait_for(timeout=35000);page.locator('[data-action="resume"]').click();assert page.locator('.winner').is_visible()
  page.locator('[data-action="more"]').click();assert page.locator('.duel').is_visible()
  page.set_viewport_size({'width':320,'height':740});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  page.screenshot(path=str(OUT/f'{engine}-small.png'),full_page=True)
  page.set_viewport_size({'width':1100,'height':900});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  assert not errors, errors
  entry={'engine':engine,'passed':True,'liveNetwork':True,'catalogueMovies':page.evaluate('catalogue.movies.length'),'providerLinks':links,'pageErrors':errors,'postersLoaded':True}
  report.append(entry)
  print(json.dumps(entry,ensure_ascii=False),flush=True)
  browser.close()
server.shutdown()
try:
 req=urllib.request.Request(public_url,headers={'User-Agent':'Seans-Prototype-Availability-Check/0.1'})
 with urllib.request.urlopen(req,timeout=40) as r:
  html=r.read().decode(); assert 'Seans' in html and 'core.js' in html and 'app.js' in html
  report.append({'publicURL':public_url,'HTTP':r.status,'contentType':r.headers.get('Content-Type'),'htmlVerified':True})
except Exception as e:
 report.append({'publicURL':public_url,'error':str(e)})
(OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

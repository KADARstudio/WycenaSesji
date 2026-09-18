"""Real-network mobile browser regression tests for Seans 0.2.
Run: pip install playwright; playwright install --with-deps chromium webkit;
python film-duel/test-v02.py. No user-account sign-in or external playback.
"""
import functools, http.server, json, os, pathlib, subprocess, threading, time, traceback
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'test-results-v02'; OUT.mkdir(exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{server.server_port}/'
PUBLIC = os.environ.get('SEANS_PUBLIC_URL', 'https://raw.githack.com/KADARstudio/WycenaSesji/seans-v02-release/film-duel/index.html')
results = []
for source in ROOT.glob('*.js'):
    subprocess.run(['node', '--check', str(source)], check=True)
unit = r"""
const a=require('node:assert/strict'), C=require('./core.js'), L=require('./ledger-v02.js');
let n=0; function test(name,f){f();n++;console.log('PASS '+name)};
const pool=Array.from({length:70},(_,i)=>({id:'m'+i,title:'Movie '+i}));
test('Winner remains on either selected side',()=>{let g=C.createGame(pool,50);g=C.choose(g,1);a.equal(g.pair[1],'m1');g=C.choose(g,0);a.equal(g.champion,'m2')});
test('Exactly fifty comparisons with unique challengers',()=>{let g=C.createGame(pool,50);let shown=new Set(g.pair);for(let i=0;i<50;i++){g=C.choose(g,0);if(g.pair[1]){a.ok(!shown.has(g.pair[1]));shown.add(g.pair[1]);}}a.equal(g.completed,50);a.ok(g.done)});
test('Pure state transitions preserve undo snapshots',()=>{let g=C.createGame(pool,10),old=JSON.stringify(g);C.choose(g,1);C.skipBoth(g);C.replace(g,0);a.equal(JSON.stringify(g),old)});
test('Two candidates finish in one decision',()=>{let g=C.choose(C.createGame(pool.slice(0,2),50),1);a.equal(g.completed,1);a.ok(g.done)});
test('Only actually defeated opponents are counted',()=>{let s=L.create(),g=C.createGame(pool,10);s.events.push({type:'pick',winner:'m0',loser:'m1'});g=C.choose(g,0);let r=L.summary(s,g);a.equal(r.defeated,1);a.equal(r.decisions,1)});
test('An unchosen last candidate is not a result',()=>{let s=L.create(),g=C.skipBoth(C.createGame(pool.slice(0,3),10));a.equal(L.result(s,g,pool[2],[],'now'),null)});
test('Repeated final rendering cannot duplicate history',()=>{let row={id:'s',movie:pool[0],stats:{measured:true,elapsedMs:2000,decisions:2}};let r=L.upsert(L.upsert([],row),row);a.equal(r.length,1)});
test('Opening a platform is not watching',()=>{a.equal(L.aggregate([{openedAt:'now',watchedAt:null,stats:{measured:false,decisions:1}}]).watched,0)});
test('Legacy session timing is not fabricated',()=>{let s=L.create(8,false),g=C.createGame(pool,10);g.completed=10;a.equal(L.summary(s,g).decisions,2);a.equal(L.summary(s,g).measured,false)});
test('Polish plural rules',()=>{a.equal(L.plural(1,'a','b','c'),'a');a.equal(L.plural(2,'a','b','c'),'b');a.equal(L.plural(12,'a','b','c'),'c');a.equal(L.plural(21,'a','b','c'),'c')});
console.log('UNIT TESTS: '+n);
"""
subprocess.run(['node', '-e', unit], cwd=ROOT, check=True)
with sync_playwright() as p:
    for engine in ['chromium','webkit']:
        browser = getattr(p,engine).launch()
        row = {'engine':engine,'passed':False,'checks':[],'errors':[]}
        results.append(row)
        ctx = browser.new_context(viewport={'width':390,'height':844}, device_scale_factor=1, is_mobile=True, has_touch=True, locale='pl-PL')
        page = ctx.new_page(); page.on('pageerror',lambda e,r=row:r['errors'].append(str(e)))
        def ok(name, condition=True):
            assert condition, name
            row['checks'].append(name)
        def ready():
            page.wait_for_function("window.SeansV02?.version === '0.2.0'", timeout=35000)
            page.wait_for_selector('[data-service="netflix"]',timeout=35000)
        def idle(): page.wait_for_function('!SeansV02.busy')
        def state(): return page.evaluate('SeansV02.snapshot()')
        try:
            page.goto(URL); ready()
            ok('audio off without creating a context',page.evaluate("!SeansFX.enabled && SeansFX.state === 'not-created'"))
            page.locator('[data-service="netflix"]').click(); page.locator('[data-service="prime"]').click()
            page.locator('[data-rounds="10"]').click()
            page.screenshot(path=str(OUT/f'{engine}-home.png'),full_page=True)
            page.locator('[data-action="start"]').click()
            first = state()['game']['pair']
            page.evaluate('window.kept=document.querySelectorAll(".duel .movie")[1]')
            page.locator('.pick[data-pick="1"]').click(); idle()
            ok('winner stays in the same DOM node and position',page.evaluate('kept===document.querySelectorAll(".duel .movie")[1]') and state()['game']['pair'][1]==first[1])
            page.locator('.pick').last.evaluate('el=>{el.click();el.click()}'); idle()
            ok('double click is counted once',state()['game']['completed']==2)
            page.locator('[data-action="undo"]').click()
            ok('undo rolls back decision and ledger',state()['game']['completed']==1 and len(state()['session']['events'])==1)
            page.locator('[data-seen="0"]').click(); idle()
            ok('seen does not add a vote',state()['game']['completed']==1)
            page.locator('[data-action="undo"]').click()
            page.locator('[data-action="skip"]').click(); idle()
            ok('skip removes both candidates without a vote',state()['game']['completed']==1 and state()['game']['champion'] is None)
            page.locator('[data-action="undo"]').click()
            page.locator('[data-detail]').first.click(); ok('movie details dialog',page.locator('dialog').is_visible()); page.locator('[data-action="close"]').click()
            try:
                page.wait_for_function("Array.from(document.querySelectorAll('.duel img')).some(i=>i.complete && i.naturalWidth>0)",timeout=15000)
                row['realPostersLoaded']=True
            except Exception: row['realPostersLoaded']=False
            page.screenshot(path=str(OUT/f'{engine}-duel.png'),full_page=True)
            page.locator('[data-v02="sound"]').click()
            page.wait_for_function("SeansFX.enabled && SeansFX.state==='running'",timeout=10000)
            ok('opt-in audio starts from a user gesture')
            page.locator('[data-v02="sound"]').click()
            before=state()['session']['elapsedMs']
            page.locator('[data-action="library"]').click()
            paused=state()['session']['elapsedMs']; page.wait_for_timeout(350)
            page.locator('[data-v02="back"]').click()
            ok('library pauses the session timer',state()['session']['elapsedMs']-paused<80)
            sid=state()['session']['id']
            page.reload(); ready(); page.locator('[data-action="resume"]').click()
            ok('reload resumes the same measured session',state()['session']['id']==sid and state()['game']['completed']==1)
            page.locator('[data-action="finish"]').click(); idle()
            ok('final contains exact stats',len(state()['rows'])==1 and state()['rows'][0]['stats']['decisions']==1 and state()['rows'][0]['stats']['defeated']==1)
            page.locator('.watch-links a').first.evaluate("el=>{el.addEventListener('click',e=>e.preventDefault(),{once:true});el.click()}")
            ok('platform opened remains separate from watched',bool(state()['rows'][0]['openedAt']) and not state()['rows'][0]['watchedAt'])
            page.screenshot(path=str(OUT/f'{engine}-winner.png'),full_page=True)
            page.locator('[data-action="save"]').click()
            page.locator('[data-v02="watched"]').click(); page.locator('[data-score="4"]').click()
            ok('explicit watched and rating',state()['rows'][0]['score']==4 and bool(state()['rows'][0]['watchedAt']))
            page.locator('[data-action="library"]').click()
            page.screenshot(path=str(OUT/f'{engine}-history.png'),full_page=True)
            with page.expect_download() as download:
                page.locator('[data-v02="export"]').click()
            ok('local JSON export',download.value.suggested_filename=='seans-moje-dane.json')
            page.locator('[data-tab="saved"]').click()
            ok('existing saved film list preserved',page.locator('.library-row').count()==1)
            page.reload(); ready(); page.locator('[data-action="library"]').click()
            ok('history and rating persist after reload',len(state()['rows'])==1 and state()['rows'][0]['score']==4)
            page.set_viewport_size({'width':320,'height':740})
            ok('320 pixel history has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.locator('[data-action="home"]').first.click(); page.locator('[data-action="start"]').click()
            page.screenshot(path=str(OUT/f'{engine}-small.png'),full_page=True)
            ok('320 pixel duel has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            for _ in range(10): page.locator('.pick').first.click(); idle()
            ok('ten round auto-final and separate sessions',state()['game']['completed']==10 and state()['screen']=='winner' and len(state()['rows'])==2)
            page.locator('[data-action="more"]').click()
            ok('continuing removes provisional duplicate',len(state()['rows'])==1 and state()['screen']=='duel')
            page.locator('.pick').first.click(); idle(); page.locator('[data-action="finish"]').click(); idle()
            ok('continued final updates the same session once',len(state()['rows'])==2 and state()['rows'][0]['stats']['decisions']==11)
            page.locator('[data-action="home"]').first.click(); page.locator('[data-action="start"]').click()
            page.evaluate("game=C.createGame([...activeMovies.values()].slice(0,3),10);SeansV02.session=SeansLedger.create();history=[];draw()")
            count=len(state()['rows']); page.locator('[data-action="skip"]').click(); idle()
            ok('last unchosen candidate is not invented selection',len(state()['rows'])==count and page.locator('[data-v02="accept"]').count()==1)
            page.locator('[data-v02="accept"]').click()
            ok('explicit acceptance records remaining candidate',len(state()['rows'])==count+1)
            reduced=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
            rp=reduced.new_page(); rp.goto(URL); rp.wait_for_selector('[data-service="netflix"]',timeout=35000)
            rp.locator('[data-service="netflix"]').click(); rp.locator('[data-action="start"]').click()
            rp.locator('.pick').first.evaluate('el=>{el.click();el.click()}'); rp.wait_for_function('!SeansV02.busy')
            ok('reduced motion keeps the input guard',rp.evaluate('!SeansFX.motion() && SeansV02.snapshot().game.completed===1'))
            reduced.close()
            page.locator('[data-action="about"]').click(); page.once('dialog',lambda d:d.accept()); page.locator('[data-action="clear-data"]').click()
            ok('clear data clears history ratings and old lists',page.evaluate('SeansV02.rows.length===0 && seen.length===0 && saved.length===0 && !SeansFX.enabled'))
            ok('no JavaScript errors',not row['errors'])
            row['catalogueMovies']=page.evaluate('catalogue.movies.length')
            row['catalogueFetchedAt']=page.evaluate('catalogue.fetchedAt')
            # Test the actual public URL, not only the checkout's local server.
            public=ctx.new_page(); public.goto(PUBLIC+'?v=020',wait_until='domcontentloaded',timeout=45000)
            public.wait_for_function("window.SeansV02?.version==='0.2.0'",timeout=45000)
            public.wait_for_selector('[data-service="netflix"]',timeout=35000)
            public.locator('[data-service="netflix"]').click(); public.locator('[data-action="start"]').click()
            public.locator('.pick').first.click();public.wait_for_function('!SeansV02.busy')
            ok('published public URL runs 0.2 and a real duel',public.evaluate('SeansV02.snapshot().game.completed===1'))
            public.screenshot(path=str(OUT/f'{engine}-public.png'),full_page=True)
            row['publicUrl']=PUBLIC; row['passed']=True
        except Exception as exc:
            row['failure']=str(exc); row['traceback']=traceback.format_exc()
            try: page.screenshot(path=str(OUT/f'{engine}-failure.png'),full_page=True)
            except Exception: pass
        finally: browser.close()
server.shutdown()
report={'version':'0.2.0','commit':os.environ.get('GITHUB_SHA'),'testedAt':datetime.now(timezone.utc).isoformat(),'unitTests':10,'results':results}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
if not all(r['passed'] for r in results): raise SystemExit(1)

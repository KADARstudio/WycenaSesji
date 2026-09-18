/* Progressive enhancement of the existing app; storage v1 remains compatible. */
(function (root) {
  'use strict';
  const L = root.SeansLedger, FX = root.SeansFX, V = root.SeansViews;
  const existing = read('history.v02', []);
  const H = { version: '0.2.0', rows: Array.isArray(existing) ? existing.filter(r => r?.id && r.movie?.title && r.stats && Array.isArray(r.movie.genres)).slice(0,200) : [], session: null, busy: false, tab: 'history', lastTick: 0 };
  root.SeansV02 = H;
  const base = { draw, start, persist, homeHTML, cardHTML, winnerHTML, libraryHTML, about };
  const saveRows = () => write('history.v02', H.rows);
  function tick() {
    const now = performance.now();
    if (H.lastTick && H.session) H.session.elapsedMs += Math.max(0, now - H.lastTick);
    H.lastTick = screen === 'duel' && !document.hidden ? now : 0;
  }
  function syncClock() { H.lastTick = screen === 'duel' && !document.hidden ? performance.now() : 0; }
  function recordResult() {
    if (!game?.done || !H.session) return;
    H.rows = L.upsert(H.rows, L.result(H.session, game, movie(game.champion), options.services, currentDate()));
    saveRows();
  }
  persist = function () {
    base.persist();
    if (game && H.session) {
      const state = read('session', null, true);
      if (state) { state.ledger = L.copy(H.session); write('session', state, true); resume = state; }
    }
  };
  homeHTML = () => base.homeHTML() + V.followup(H);
  cardHTML = function (id, side) {
    const streak = game.champion === id && game.wins ? `✦ ${game.wins} ${L.plural(game.wins, 'zwycięstwo', 'zwycięstwa', 'zwycięstw')} z rzędu` : 'Nowy przeciwnik';
    return base.cardHTML(id, side).replace('<h2>', `<div class="streak-line ${game.champion === id ? 'is-champion' : ''}">${esc(streak)}</div><h2>`);
  };
  winnerHTML = () => V.winner(H, base.winnerHTML);
  libraryHTML = () => V.library(H, base.libraryHTML);
  draw = function () { base.draw(); FX.control(); };
  about = function () {
    base.about();
    const box = $('#sheet-content');
    box.innerHTML = box.innerHTML.replace('WERSJA 0.1', 'WERSJA 0.2.0') + '<h3>Animacje i statystyki</h3><p>Dźwięki włączasz ikoną nuty. Ograniczanie ruchu respektuje ustawienia urządzenia. Historia i oceny zostają wyłącznie w tej przeglądarce. Czas mierzymy, gdy widoczny jest ekran pojedynków; wejście do biblioteki i ukrycie strony wstrzymuje pomiar. Kliknięcie platformy nigdy nie oznacza automatycznie obejrzenia filmu.</p>';
  };
  function snapshot() {
    history.push({ game: L.copy(game), seen: seen.slice(), events: L.copy(H.session.events), entry: L.copy(H.rows.find(r => r.id === H.session.id) || null) });
    if (history.length > 100) history.shift();
  }
  function append(event) { H.session.events.push({ ...event, at: new Date().toISOString() }); }
  function startSession() {
    tick(); H.session = L.create(); history = [];
    base.start(); syncClock(); persist();
  }
  function paintPair() {
    const template = document.createElement('template');
    template.innerHTML = duelHTML();
    const fresh = template.content;
    for (const selector of ['.duel-top', '.duel-title', '.duel-actions', '.duel-end']) {
      const old = $(selector), next = fresh.querySelector(selector);
      if (old && next) old.innerHTML = next.innerHTML;
    }
    $('.progress > div').style.width = `${Math.round(game.completed / game.goal * 100)}%`;
    const oldCards = [...document.querySelectorAll('.duel .movie')];
    [...fresh.querySelectorAll('.movie')].forEach((next, side) => {
      const old = oldCards[side];
      if (old && old.dataset.movie === next.dataset.movie) {
        for (const selector of ['.poster-badge', '.streak-line']) {
          const target = old.querySelector(selector), source = next.querySelector(selector);
          target.className = source.className; target.innerHTML = source.innerHTML;
        }
        old.classList.remove('picked-card');
      } else if (old) {
        old.replaceWith(next);
        FX.animate(next, [{ opacity: 0, transform: `translateX(${side ? 22 : -22}px)` }, { opacity: 1, transform: 'translateX(0)' }], 140);
      }
    });
    document.querySelectorAll('.movie img').forEach(img => img.addEventListener('error', () => img.remove(), { once: true }));
    preload();
  }
  function preload() {
    if (!game) return;
    game.deck.slice(game.cursor, game.cursor + 2).forEach(id => {
      const url = safeURL(movie(id)?.poster);
      if (url) { const img = new Image(); img.referrerPolicy = 'no-referrer'; img.src = url; }
    });
  }
  async function move(kind, side) {
    if (H.busy || !game || screen !== 'duel' || game.done) return;
    H.busy = true; tick(); FX.unlock();
    snapshot();
    const cards = [...document.querySelectorAll('.duel .movie')];
    const oldChampion = game.champion;
    let winnerRect = null;
    try {
      if (kind === 'pick') {
        const winner = game.pair[side], loser = game.pair[1-side];
        winnerRect = cards[side]?.querySelector('.poster-wrap').getBoundingClientRect();
        append({ type: 'pick', winner, loser });
        game = C.choose(game, side); cards[side]?.classList.add('picked-card'); FX.play('pick');
        await FX.animate(cards[1-side], [{ opacity: 1, transform: 'translateX(0)' }, { opacity: 0, transform: `translateX(${side ? -30 : 30}px) scale(.96)` }], 150);
      } else if (kind === 'seen') {
        const id = game.pair[side]; append({ type: 'seen', id });
        if (!seen.includes(id)) seen.push(id); write('seen', seen);
        game = C.replace(game, side); FX.play('shift');
        await FX.animate(cards[side], [{ opacity: 1 }, { opacity: 0, transform: 'translateY(12px)' }], 150);
      } else if (kind === 'skip') {
        append({ type: 'skip', ids: game.pair.slice() }); game = C.skipBoth(game); FX.play('shift');
        await Promise.all(cards.map(el => FX.animate(el, [{ opacity: 1 }, { opacity: 0, transform: 'translateY(14px)' }], 150)));
      } else if (kind === 'finish' && game.champion) {
        winnerRect = cards.find(el => el.dataset.movie === game.champion)?.querySelector('.poster-wrap').getBoundingClientRect();
        game.done = true;
      }
      tick(); screen = game.done ? 'winner' : 'duel'; syncClock();
      recordResult(); persist();
      if (game.done) {
        draw(); window.scrollTo(0,0); FX.play('finish');
        const el = $('.winner .poster-wrap');
        if (el && winnerRect) {
          const rect = el.getBoundingClientRect();
          FX.animate(el, [{ transform: `translate(${winnerRect.x-rect.x}px,${winnerRect.y-rect.y}px) scale(${winnerRect.width/rect.width})` }, { transform: 'translate(0,0) scale(1)' }], 300);
        }
        FX.animate($('.winner h1'), [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'translateY(0)' }], 260);
      } else {
        paintPair();
        if (kind === 'pick' && oldChampion && oldChampion !== game.champion) notify('Nowy faworyt!');
        if (kind === 'seen') notify('Obejrzany — podmieniam tylko ten film.');
      }
      /* Keep an input guard even when reduced motion disables all animation. */
      await new Promise(resolve => setTimeout(resolve, FX.motion() ? 140 : 240));
    } finally { H.busy = false; }
  }
  function undo() {
    if (!history.length || !game || H.busy) return;
    tick(); const h = history.pop();
    game = h.game; seen = h.seen; H.session.events = h.events || [];
    H.rows = H.rows.filter(r => r.id !== H.session.id);
    if (h.entry) H.rows = L.upsert(H.rows, h.entry);
    write('seen', seen); saveRows();
    screen = game.done ? 'winner' : 'duel'; syncClock(); persist(); draw(); FX.play('shift');
  }
  function updateRow(id, change) {
    const row = H.rows.find(r => r.id === id); if (!row) return;
    change(row); saveRows(); draw();
  }
  function exportData() {
    const body = JSON.stringify({ app: 'Seans', version: H.version, exportedAt: new Date().toISOString(), history: H.rows, saved, seen, options }, null, 2);
    const url = URL.createObjectURL(new Blob([body], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'seans-moje-dane.json';
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
  function clearAll() {
    if (!confirm('Usunąć ustawienia, historię, oceny, obejrzane i zapisane filmy z tej przeglądarce?')) return;
    tick(); FX.reset(); H.rows = []; H.session = null; H.lastTick = 0; saveRows();
    seen = []; saved = []; game = null; history = []; resume = null;
    options = { services: [], rounds: 25, genre: '', runtime: '', rating: '', year: '' };
    write('seen',seen); write('saved',saved); saveOptions(); write('session',null,true);
    $('#sheet').close(); screen = catalogue ? 'home' : 'error'; draw(); notify('Twoje lokalne dane zostały usunięte.');
  }
  document.addEventListener('click', event => {
    const el = event.target.closest('button,a'); if (!el) return;
    const d = el.dataset;
    if (d.v02) {
      event.preventDefault(); event.stopImmediatePropagation();
      if (H.busy && d.v02 !== 'sound') return;
      switch (d.v02) {
        case 'sound': FX.toggle(); break;
        case 'tab': H.tab = d.tab; draw(); break;
        case 'back': tick(); screen = game && !game.done ? 'duel' : 'home'; syncClock(); draw(); break;
        case 'export': exportData(); break;
        case 'dismiss': updateRow(d.id, row => row.followupDismissed = true); break;
        case 'watched': updateRow(d.id, row => {
          if (row.watchedAt) {
            row.watchedAt = null; row.score = null;
            if (row.addedToSeen && !H.rows.some(r => r.id !== row.id && r.movie.id === row.movie.id && r.watchedAt)) seen = seen.filter(id => id !== row.movie.id);
            row.addedToSeen = false;
          } else {
            row.watchedAt = new Date().toISOString(); row.addedToSeen = !seen.includes(row.movie.id);
            if (row.addedToSeen) seen.push(row.movie.id);
          }
          write('seen',seen);
        }); break;
        case 'rate': updateRow(d.id, row => { if (row.watchedAt) row.score = Number(d.score); }); break;
        case 'delete-record': if (confirm('Usunąć ten wpis z historii?')) { H.rows = H.rows.filter(r => r.id !== d.id); saveRows(); draw(); } break;
        case 'clear-history': if (confirm('Usunąć historię seansów i oceny? Lista na później zostanie.')) { H.rows = []; saveRows(); draw(); } break;
        case 'accept': if (game?.champion && H.session) { append({ type:'accept', winner:game.champion }); recordResult(); persist(); draw(); FX.play('finish'); } break;
      }
      return;
    }
    const intercepted = d.pick !== undefined || d.seen !== undefined || ['start','undo','skip','finish','more','resume','clear-data'].includes(d.action);
    if (H.busy) { event.preventDefault(); event.stopImmediatePropagation(); return; }
    if (intercepted) {
      event.preventDefault(); event.stopImmediatePropagation();
      if (el.disabled) return;
      if (d.pick !== undefined) { void move('pick', Number(d.pick)); return; }
      if (d.seen !== undefined) { void move('seen', Number(d.seen)); return; }
      switch (d.action) {
        case 'start': startSession(); preload(); break;
        case 'undo': undo(); break;
        case 'skip': void move('skip'); break;
        case 'finish': void move('finish'); break;
        case 'more': if (game && game.pair.every(Boolean)) {
          tick(); H.rows = H.rows.filter(r => r.id !== H.session?.id); saveRows();
          game = C.continueGame(game); screen = 'duel'; syncClock(); persist(); draw(); window.scrollTo(0,0);
        } break;
        case 'resume': if (resume?.pool?.length >= 2) {
          activeMovies = new Map(resume.pool.map(m => [m.id,m])); game = resume.game; options = resume.options; history = [];
          gameFetchedAt = resume.fetchedAt; H.session = resume.ledger || L.create(game.completed, false);
          screen = game.done ? 'winner' : 'duel'; syncClock(); persist(); draw();
        } break;
        case 'clear-data': clearAll(); break;
      }
      return;
    }
    if (el.matches('.watch-links a') && screen === 'winner' && H.session) {
      const row = H.rows.find(r => r.id === H.session.id);
      if (row) { row.openedAt = row.openedAt || new Date().toISOString(); saveRows(); }
    }
    if (['home','library','reload'].includes(d.action)) { tick(); persist(); H.lastTick = 0; }
  }, true);
  document.addEventListener('visibilitychange', () => { tick(); persist(); });
  root.addEventListener('pagehide', () => { tick(); H.lastTick = 0; persist(); });
  root.addEventListener('pageshow', () => { syncClock(); });
  const header = document.querySelector('.header-right');
  const sound = document.createElement('button'); sound.className = 'icon-btn sound-button'; sound.dataset.v02 = 'sound';
  header.insertBefore(sound, header.firstChild); FX.control();
  document.querySelector('.beta').textContent = '0.2 BETA';
  const libraryButton = document.querySelector('[data-action="library"]');
  libraryButton.setAttribute('aria-label','Moje seanse i statystyki'); libraryButton.title = 'Moje seanse i statystyki'; libraryButton.textContent = '▥';
  H.snapshot = () => ({ version: H.version, screen, game: game ? L.copy(game) : null, session: H.session ? L.copy(H.session) : null, rows: L.copy(H.rows), busy: H.busy, sound: FX.enabled });
  if (screen !== 'loading') draw();
})(window);

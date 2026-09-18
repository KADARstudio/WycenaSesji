/* Presentation for local history. User-provided text is escaped by the app. */
(function (root) {
  'use strict';
  const L = root.SeansLedger;
  const tile = (value, label) => `<div class="stat-tile"><strong>${esc(value)}</strong><span>${label}</span></div>`;
  function stats(s) {
    return `<div class="session-stats">${tile(s.measured ? L.duration(s.elapsedMs) : '—', 'czas wyboru')}${tile(s.decisions, 'decyzje')}${tile(s.defeated, 'pokonani przez zwycięzcę')}</div><p class="metric-note">${s.measured ? 'Czas na widocznym ekranie pojedynków, bez czasu poza aplikacją.' : 'Sesja rozpoczęta w starszej wersji. Statystyki tylko od wznowienia.'}</p>`;
  }
  function review(row) {
    if (!row) return '';
    return `<div class="review-box" data-record="${esc(row.id)}"><div class="review-top"><strong>${row.watchedAt ? '✓ Obejrzany' : 'Udało się obejrzeć?'}</strong><button class="text-btn" data-v02="watched" data-id="${esc(row.id)}">${row.watchedAt ? 'Cofnij oznaczenie' : 'Tak, obejrzany'}</button></div>${row.watchedAt ? `<div class="review-score"><span>Twoja ocena</span><div class="rating-buttons">${[1,2,3,4,5].map(n => `<button data-v02="rate" data-id="${esc(row.id)}" data-score="${n}" aria-label="Ocena ${n} z 5" aria-pressed="${row.score === n}">${n} ★</button>`).join('')}</div></div>` : '<p>Otwarcie platformy nie oznacza obejrzenia filmu.</p>'}</div>`;
  }
  function library(H, legacy) {
    const a = L.aggregate(H.rows);
    const heading = `<section class="seans-history"><div class="eyebrow">TWÓJ WIECZÓR, TWOJE WYBORY</div><h1>Moje seanse.</h1><p class="help-line left">Historia tylko w tej przeglądarce. Bez konta i bez wysyłania Twoich wyborów na serwer.</p><div class="history-stats">${tile(a.chosen,'wybrane')}${tile(a.opened,'otwarcia platformy')}${tile(a.watched,'obejrzane')}${tile(a.averageMs === null ? '—' : L.duration(a.averageMs),'średni czas wyboru')}</div><div class="history-tabs" role="tablist" aria-label="Moje filmy"><button role="tab" data-v02="tab" data-tab="history" aria-selected="${H.tab === 'history'}">Historia (${H.rows.length})</button><button role="tab" data-v02="tab" data-tab="saved" aria-selected="${H.tab === 'saved'}">Na później (${saved.length})</button></div>`;
    if (H.tab === 'saved') return heading + legacy().replace('<h1>Na kolejny wieczór.</h1>', '<h2>Na kolejny wieczór.</h2>') + '</section>';
    const entries = H.rows.map(row => `<article class="history-card"><div class="history-head">${image(row.movie,'history-poster')}<div><div class="eyebrow">${esc(dateText(row.chosenAt))}</div><h2>${esc(row.movie.title)}</h2><p>${esc(meta(row.movie))}</p><div class="history-status">${row.watchedAt ? '✓ Obejrzany' : row.openedAt ? '↗ Otwarto platformę' : '✦ Wybrany'}${row.score ? ` · ${row.score}/5 ★` : ''}</div></div></div><div class="history-metrics">${row.stats.decisions} ${L.plural(row.stats.decisions,'decyzja','decyzje','decyzji')} · ${row.stats.measured ? esc(L.duration(row.stats.elapsedMs)) : 'czas niepełny'} · zwycięzca pokonał ${row.stats.defeated}</div><a class="inline-link" href="${esc(safeURL(row.movie.url))}" target="_blank" rel="noopener noreferrer">Sprawdź aktualną dostępność ↗</a>${review(row)}<button class="text-btn" data-v02="delete-record" data-id="${esc(row.id)}">Usuń ten seans</button></article>`).join('');
    return heading + (entries || '<div class="history-empty"><span>✦</span><h2>Pierwszy seans przed Tobą.</h2><p>Wybierz film. Tutaj zapisze się finał i Twoje prawdziwe statystyki.</p></div>') + `<div class="history-actions"><button class="primary" data-v02="back">${game && !game.done ? 'Wróć do pojedynków' : 'Wybierz film'}</button><button class="secondary" data-v02="export">Eksportuj historię</button>${H.rows.length ? '<button class="text-btn danger" data-v02="clear-history">Usuń historię seansów</button>' : ''}</div><p class="help-line">Do 200 ostatnich sesji. Eksport to kopia JSON, nie synchronizacja między telefonami.</p></section>`;
  }
  function winner(H, legacy) {
    if (!game?.champion) return legacy();
    const s = L.summary(H.session, game);
    const row = H.rows.find(r => r.id === H.session?.id);
    let html = legacy().replace('Dziś oglądasz.', s.chosen ? 'Mamy film.' : 'Ostatni kandydat.');
    html = html.replace(/<p class="winner-intro">[\s\S]*?<\/p>/, `<p class="winner-intro">${s.chosen ? 'Koniec szukania. Czas na dobry wieczór.' : 'Pozostał jeden film. Potwierdź, czy to Twój wybór.'}</p>`);
    html = html.replace('<div class="winner-actions">', `${s.chosen ? stats(s) + review(row) : '<button class="primary" data-v02="accept">Wybieram ten film ✓</button>'}<div class="winner-actions">`);
    return html;
  }
  function followup(H) {
    const row = H.rows.find(r => !r.watchedAt && !r.followupDismissed);
    if (!row) return '';
    return `<aside class="followup"><div><span class="eyebrow">OSTATNI WYBÓR</span><strong>${esc(row.movie.title)}</strong><p>Udało się obejrzeć?</p></div><div><button class="secondary" data-v02="watched" data-id="${esc(row.id)}">Tak ✓</button><button class="text-btn" data-v02="dismiss" data-id="${esc(row.id)}">Nie teraz</button></div></aside>`;
  }
  root.SeansViews = { stats, review, library, winner, followup };
})(window);

/* Original, optional synthesized effects; no audio downloads or recording. */
(function (root) {
  'use strict';
  let enabled = read('sound', false) === true;
  let context = null, epoch = 0;
  const motion = () => !root.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function control() {
    const el = document.querySelector('[data-v02="sound"]');
    if (!el) return;
    el.textContent = enabled ? '♪' : '♪̸';
    el.setAttribute('aria-pressed', String(enabled));
    el.setAttribute('aria-label', enabled ? 'Wyłącz dźwięki' : 'Włącz dźwięki');
    el.title = enabled ? 'Dźwięki włączone' : 'Dźwięki wyłączone';
  }
  function unlock() {
    if (!enabled) return;
    try {
      const Audio = root.AudioContext || root.webkitAudioContext;
      if (!Audio) return;
      if (!context || context.state === 'closed') context = new Audio();
      if (context.state !== 'running') context.resume().catch(() => {});
    } catch (_) { /* The app still works when audio is unavailable. */ }
  }
  function note(frequency, delay, length, volume, end) {
    const o = context.createOscillator(), g = context.createGain();
    const t = context.currentTime + delay;
    o.type = 'sine';
    o.frequency.setValueAtTime(frequency, t);
    if (end) o.frequency.exponentialRampToValueAtTime(end, t + length);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(volume, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + length);
    o.connect(g); g.connect(context.destination);
    o.start(t); o.stop(t + length + 0.02);
    o.onended = () => { o.disconnect(); g.disconnect(); };
  }
  function play(kind = 'pick') {
    if (!enabled) return;
    unlock();
    const current = epoch;
    if (!context) return;
    Promise.resolve(context.state === 'running' ? null : context.resume()).then(() => {
      if (!enabled || current !== epoch || context.state !== 'running') return;
      if (kind === 'finish') {
        [523.25, 659.25, 783.99].forEach((f, i) => note(f, i * 0.065, 0.26, 0.042));
      } else if (kind === 'shift') {
        note(230, 0, 0.09, 0.028, 95);
      } else {
        note(620, 0, 0.08, 0.052, 420);
      }
    }).catch(() => {});
  }
  function toggle() {
    enabled = !enabled; epoch++;
    write('sound', enabled); control();
    if (enabled) play('pick');
    else if (context?.state === 'running') context.suspend().catch(() => {});
    return enabled;
  }
  async function animate(el, frames, duration = 180) {
    if (!el || !motion() || typeof el.animate !== 'function') return;
    const animation = el.animate(frames, { duration, easing: 'cubic-bezier(.2,.7,.2,1)' });
    try { await animation.finished; } catch (_) {}
  }
  root.SeansFX = { play, unlock, toggle, control, motion, animate,
    reset() { if (enabled) toggle(); },
    get enabled() { return enabled; },
    get state() { return context?.state || 'not-created'; } };
})(window);

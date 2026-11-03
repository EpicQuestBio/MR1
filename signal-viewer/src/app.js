import { MR1Stream, SAMPLE_RATE, BUFFER_SECONDS, makeMR1Frame } from './signal.js';

const $ = id => document.getElementById(id);
const stream = new MR1Stream();
const plot = $('signalCanvas');
const ctx = plot.getContext('2d', { alpha: false });
const area = $('chartArea');
const tooltip = $('chartTooltip');
const GRID = { left: 63, right: 18, top: 23, bottom: 43 };
const COLORS = {
  bg: '#101c27', plot: '#0d1923', grid: '#223845', axis: '#738f9e',
  wave: '#65ddce', waveLow: '#36aead', baseline: '#d6ad6b',
  event: '#f1a27e', cross: '#9bb5bd', selection: '#eac078',
};
const intFmt = new Intl.NumberFormat('en-US');
let source = null;     // WebSocket | DemoSource | null
let sourceType = null; // 'ws' | 'demo' | null
let state = 'offline';
let windowSeconds = 5;
let followLive = true;
let autoScale = true;
let showMarkers = true;
let viewportEnd = 0;
let fixedYRange = null;
let dimensions = { width: 0, height: 0, dpr: 1 };
let pointer = null;
let dragging = null;
let dirty = true;
let lastPaint = 0;
let samplesThisSecond = 0;
let throughput = 0;
let lastPacketAt = 0;
let selectedEvent = null;
let lastError = '';

function setStatus(next, explanation = '') {
  state = next;
  const names = { offline: 'Disconnected', connecting: 'Connecting', connected: 'Connected', demo: 'Local demo', error: 'Connection error' };
  $('connectionLabel').textContent = names[next];
  $('connectionDot').className = 'status-dot' + (next === 'connected' || next === 'demo' ? ' online' : next === 'connecting' ? ' connecting' : next === 'error' ? ' error' : '');
  $('connectionHelp').textContent = explanation || (next === 'connected' ? 'Binary MR1 frames are arriving from the bridge.' : next === 'demo' ? 'Synthetic two-sample events; encoded and decoded using the real MR1 binary frame format.' : 'Connect to the MR1 Python bridge or explore a simulated two-sample blockade stream.');
  $('connectBtn').disabled = next === 'connecting' || next === 'connected';
  $('disconnectBtn').disabled = !source;
  $('demoBtn').disabled = next === 'demo';
  $('emptyState').hidden = next === 'connected' || next === 'demo' || stream.received > 0;
  $('liveBtn').textContent = followLive ? '◉ Live' : '◎ Return live';
  $('footerStatus').textContent = next === 'demo' ? 'LOCAL DEMO / 100 kHz' : next === 'connected' ? 'BRIDGE / ws stream' : next === 'connecting' ? 'OPENING SOCKET' : next === 'error' ? 'WEBSOCKET ERROR' : 'NO ACTIVE SOURCE';
  dirty = true;
}

function resetSession() {
  stream.reset();
  stream.detector.thresholdPA = Number($('thresholdInput').value);
  samplesThisSecond = 0; throughput = 0; selectedEvent = null;
  viewportEnd = 0; fixedYRange = null; followLive = true;
  $('followCheck').checked = true;
  updateStatistics();
  dirty = true;
}

function stopSource(silent = false) {
  if (sourceType === 'ws' && source) {
    source.onopen = source.onclose = source.onerror = source.onmessage = null;
    source.close();
  } else if (sourceType === 'demo' && source) {
    source.stop();
  }
  source = null;
  sourceType = null;
  if (!silent) setStatus('offline');
}

function consumePacket(buffer) {
  try {
    const result = stream.ingestPacket(buffer);
    if (result.ignored) return;
    samplesThisSecond += result.samples;
    lastPacketAt = performance.now();
    dirty = true;
  } catch (err) {
    lastError = err.message;
    $('connectionHelp').textContent = `Ignored invalid frame: ${err.message}`;
    console.warn('MR1 frame:', err);
  }
}

function connectWebSocket() {
  lastError = '';
  stopSource(true);
  resetSession();
  const url = $('socketUrl').value.trim();
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'ws:' && parsed.protocol !== 'wss:') throw new Error('Use a ws:// or wss:// URL.');
    source = new WebSocket(url);
  } catch (error) {
    source = null;
    setStatus('error', error.message);
    return;
  }
  sourceType = 'ws';
  const ws = source;
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => {
    if (source !== ws) return;
    setStatus('connected', `Connected to ${url}. Waiting for MR1 binary frames…`);
  };
  ws.onmessage = event => {
    if (source !== ws) return;
    if (event.data instanceof ArrayBuffer) consumePacket(event.data);
    else if (event.data instanceof Blob) event.data.arrayBuffer().then(buffer => { if (source === ws) consumePacket(buffer); });
  };
  ws.onerror = () => {
    if (source !== ws) return;
    lastError = 'WebSocket connection failed. Is websocket_bridge.py running?';
  };
  ws.onclose = event => {
    if (source !== ws) return;
    source = null;
    sourceType = null;
    setStatus('error', lastError || `WebSocket closed (code ${event.code}). Verify the bridge and address.`);
    lastError = '';
  };
  setStatus('connecting', `Opening ${url}…`);
}

class DemoSource {
  constructor(onFrame) {
    this.onFrame = onFrame;
    this.sample = 0;
    this.pending = 0;
    this.eventRemaining = 0;
    this.eventDepth = 32;
    this.timer = null;
    this.lastTime = 0;
  }
  start() {
    this.lastTime = performance.now();
    this.timer = setInterval(() => this.tick(), 16);
  }
  tick() {
    const now = performance.now();
    // Clamp elapsed wall-clock time to keep browser-background throttling from
    // creating an unbounded backlog. This is a demonstration, not an acquisition clock.
    this.pending += Math.min(100, now - this.lastTime) * SAMPLE_RATE / 1000;
    this.lastTime = now;
    let frames = 0;
    while (this.pending >= 64 && frames < 160) {
      const values = new Float32Array(64);
      for (let i = 0; i < 64; i++) {
        const time = (this.sample + i) / SAMPLE_RATE;
        const baseline = 122 + 7 * Math.sin(time * 0.75) + 3.6 * Math.sin(time * 3.1);
        const noise = (Math.random() + Math.random() + Math.random() - 1.5) * 4.4;
        if (this.eventRemaining === 0 && Math.random() < 0.00036) {
          this.eventRemaining = 2;
          this.eventDepth = 26 + Math.random() * 22;
        }
        let current = baseline + noise;
        if (this.eventRemaining > 0) { current -= this.eventDepth; this.eventRemaining--; }
        values[i] = current;
      }
      const timestamp = BigInt(this.sample * 10);
      this.onFrame(makeMR1Frame(timestamp, values));
      this.sample += 64;
      this.pending -= 64;
      frames++;
    }
  }
  stop() { clearInterval(this.timer); this.timer = null; }
}

function startDemo() {
  stopSource(true);
  resetSession();
  source = new DemoSource(consumePacket);
  sourceType = 'demo';
  source.start();
  setStatus('demo');
}

function formatElapsed(seconds, digits = 3) {
  if (Math.abs(seconds) < 1) return `${(seconds * 1000).toFixed(Math.abs(seconds) < 0.01 ? 2 : 1)} ms`;
  return `${seconds.toFixed(digits)} s`;
}
function formatPA(value, decimals = 1) {
  return Number.isFinite(value) ? value.toFixed(decimals) : '—';
}
function windowSamples() { return Math.max(10, Math.round(windowSeconds * SAMPLE_RATE)); }
function clamp(value, lo, hi) { return Math.min(hi, Math.max(lo, value)); }
function getView() {
  const history = stream.history;
  const latest = history.nextIndex - 1;
  const span = windowSamples();
  if (latest < 0) return { start: -span, end: 0, span };
  const earliestAllowedEnd = Math.min(latest, history.oldestIndex + span - 1);
  const end = followLive ? latest : clamp(viewportEnd, earliestAllowedEnd, latest);
  if (!followLive) viewportEnd = end;
  return { start: end - span + 1, end, span };
}

function setWindow(seconds, preserveAnchor = false, fraction = 0.5) {
  const old = getView();
  const anchor = old.start + old.span * fraction;
  windowSeconds = clamp(seconds, 0.0005, BUFFER_SECONDS);
  const select = $('windowSelect');
  const matching = [...select.options].find(x => Math.abs(Number(x.value) - windowSeconds) < 1e-9);
  const custom = $('customWindowOption');
  if (matching) { if (custom) custom.remove(); select.value = matching.value; }
  else {
    if (custom) custom.remove();
    const option = document.createElement('option');
    option.id = 'customWindowOption'; option.value = String(windowSeconds);
    option.textContent = `${formatElapsed(windowSeconds)} · custom`;
    select.add(option); select.value = option.value;
  }
  if (preserveAnchor) {
    followLive = false;
    $('followCheck').checked = false;
    viewportEnd = anchor + windowSamples() * (1 - fraction);
  }
  fixedYRange = null;
  dirty = true;
}

function goLive() {
  followLive = true;
  $('followCheck').checked = true;
  selectedEvent = null;
  dirty = true;
}

function getBox() {
  return {
    x: GRID.left, y: GRID.top,
    w: Math.max(1, dimensions.width - GRID.left - GRID.right),
    h: Math.max(1, dimensions.height - GRID.top - GRID.bottom),
  };
}
function graphX(sample, view, box) { return box.x + (sample - view.start) / view.span * box.w; }
function graphY(value, range, box) { return box.y + box.h - (value - range.min) / (range.max - range.min) * box.h; }

function drawCanvas() {
  if (!dimensions.width || !dimensions.height || !ctx) return;
  const { width, height, dpr } = dimensions;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, width, height);
  const box = getBox();
  ctx.fillStyle = COLORS.plot;
  ctx.fillRect(box.x, box.y, box.w, box.h);
  const view = getView();
  const history = stream.history;
  const rawMode = view.span <= box.w * 1.6;
  const dataLeft = Math.max(history.oldestIndex, Math.floor(view.start));
  const dataRight = Math.min(history.nextIndex, Math.ceil(view.end + 1));
  const columns = [];
  let lo = Infinity, hi = -Infinity;

  if (rawMode) {
    for (let s = dataLeft; s < dataRight; s++) {
      const v = history.get(s);
      if (Number.isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; }
    }
  } else if (dataRight > dataLeft) {
    const visibleWidth = Math.ceil(box.w);
    for (let px = 0; px < visibleWidth; px++) {
      const a = Math.floor(view.start + (px / box.w) * view.span);
      const b = Math.max(a + 1, Math.ceil(view.start + ((px + 1) / box.w) * view.span));
      const mm = history.range(a, b);
      columns.push(mm);
      if (mm) { if (mm.min < lo) lo = mm.min; if (mm.max > hi) hi = mm.max; }
    }
  }

  if (!Number.isFinite(lo)) { lo = 0; hi = 200; }
  const pad = Math.max(3, (hi - lo) * .18);
  const newRange = { min: lo - pad, max: hi + pad };
  if (autoScale || !fixedYRange) fixedYRange = newRange;
  const range = autoScale ? newRange : fixedYRange;

  // Grid and readable axes.
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.lineWidth = 1;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 5; i++) {
    const y = box.y + box.h * i / 5;
    ctx.strokeStyle = COLORS.grid;
    ctx.beginPath(); ctx.moveTo(box.x, y + .5); ctx.lineTo(box.x + box.w, y + .5); ctx.stroke();
    ctx.fillStyle = COLORS.axis;
    ctx.fillText((range.max - (range.max - range.min) * i / 5).toFixed(1), box.x - 11, y);
  }
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let i = 0; i <= 6; i++) {
    const x = box.x + box.w * i / 6;
    ctx.strokeStyle = COLORS.grid;
    ctx.beginPath(); ctx.moveTo(x + .5, box.y); ctx.lineTo(x + .5, box.y + box.h); ctx.stroke();
    const sec = (view.start + view.span * i / 6) / SAMPLE_RATE;
    ctx.fillStyle = COLORS.axis;
    ctx.fillText(sec < 0 ? '' : windowSeconds < .1 ? `${(sec * 1000).toFixed(2)} ms` : `${sec.toFixed(windowSeconds < 1 ? 3 : 2)} s`, x, box.y + box.h + 11);
  }
  ctx.save(); ctx.translate(12, box.y + box.h * 0.5); ctx.rotate(-Math.PI / 2);
  ctx.font = '10px ui-sans-serif, system-ui'; ctx.fillStyle = '#829aab';
  ctx.textAlign = 'center'; ctx.fillText('CURRENT (pA)', 0, 0); ctx.restore();

  // Clipping means spikes cannot draw across axes or toolbar.
  ctx.save();
  ctx.beginPath(); ctx.rect(box.x, box.y, box.w, box.h); ctx.clip();

  // Baseline reference (only drawn when we have current data).
  if (history.availableSamples && Number.isFinite(stream.detector.baseline)) {
    const y = graphY(stream.detector.baseline, range, box);
    ctx.strokeStyle = COLORS.baseline;
    ctx.globalAlpha = .72;
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 6]);
    ctx.beginPath(); ctx.moveTo(box.x, y); ctx.lineTo(box.x + box.w, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }

  if (rawMode) {
    ctx.strokeStyle = COLORS.wave; ctx.lineWidth = 1.5;
    ctx.beginPath(); let started = false;
    for (let s = dataLeft; s < dataRight; s++) {
      const v = history.get(s);
      if (!Number.isFinite(v)) { started = false; continue; }
      const x = graphX(s, view, box), y = graphY(v, range, box);
      if (!started) { ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    if (view.span < box.w / 4) {
      ctx.fillStyle = '#a4f9e9';
      for (let s = dataLeft; s < dataRight; s++) {
        const v = history.get(s);
        if (!Number.isFinite(v)) continue;
        ctx.beginPath(); ctx.arc(graphX(s, view, box), graphY(v, range, box), 2.8, 0, Math.PI * 2); ctx.fill();
      }
    }
  } else {
    // An extrema segment for EACH screen pixel: the briefest downward blockade
    // is retained without pretending that multiple extrema have known ordering.
    ctx.strokeStyle = COLORS.wave; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x < columns.length; x++) {
      const mm = columns[x]; if (!mm) continue;
      const xx = box.x + x + .5;
      ctx.moveTo(xx, graphY(mm.min, range, box));
      ctx.lineTo(xx, graphY(mm.max, range, box));
    }
    ctx.stroke();
  }

  const visibleEvents = stream.detector.events.filter(ev => ev.startSample >= view.start - ev.durationSamples && ev.startSample <= view.end + 1);
  const markersSuppressed = visibleEvents.length > 240;
  if (showMarkers && !markersSuppressed) {
    for (const ev of visibleEvents) {
      const x = graphX(ev.startSample, view, box);
      const y = clamp(graphY(ev.minPA, range, box), box.y + 5, box.y + box.h - 5);
      ctx.fillStyle = COLORS.event;
      ctx.beginPath(); ctx.arc(x, y, rawMode ? 4 : 2.6, 0, Math.PI * 2); ctx.fill();
    }
  }
  if (selectedEvent !== null && selectedEvent >= view.start && selectedEvent <= view.end) {
    const x = graphX(selectedEvent, view, box);
    ctx.strokeStyle = COLORS.selection; ctx.lineWidth = 1.3; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(x, box.y); ctx.lineTo(x, box.y + box.h); ctx.stroke(); ctx.setLineDash([]);
  }
  if (pointer && pointer.x >= box.x && pointer.x <= box.x + box.w && pointer.y >= box.y && pointer.y <= box.y + box.h) {
    ctx.strokeStyle = COLORS.cross; ctx.globalAlpha = .5;
    ctx.lineWidth = 1; ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(pointer.x, box.y); ctx.lineTo(pointer.x, box.y + box.h); ctx.moveTo(box.x, pointer.y); ctx.lineTo(box.x + box.w, pointer.y); ctx.stroke();
    ctx.setLineDash([]); ctx.globalAlpha = 1;
  }
  ctx.restore();

  if (pointer && history.availableSamples > 0) updateTooltip(pointer, view, box);
  else tooltip.hidden = true;
  const detail = rawMode ? 'RAW SAMPLES' : 'MIN / MAX DECIMATION';
  $('viewInfo').textContent = `${detail}  ·  ${formatElapsed(windowSeconds)} window  ·  ${(view.span / box.w).toFixed(view.span / box.w < 10 ? 2 : 0)} samples / px` + (markersSuppressed && showMarkers ? '  ·  Event markers hidden at this scale' : '');
  $('plotMode').textContent = followLive ? 'LIVE' : 'HISTORY';
  $('plotMode').className = 'plot-mode' + (followLive ? '' : ' historical');
  document.querySelector('.live-ring').classList.toggle('active', state === 'connected' || state === 'demo');
}

function updateTooltip(pos, view, box) {
  const index = Math.floor(view.start + (pos.x - box.x) / box.w * view.span);
  const value = stream.history.get(index);
  const bucketWidth = Math.max(1, Math.round(view.span / box.w));
  const range = stream.history.range(index - Math.floor(bucketWidth / 2), index + Math.ceil(bucketWidth / 2));
  const label = range && bucketWidth > 1 ? `<div>Range: <strong>${formatPA(range.min)} – ${formatPA(range.max)} pA</strong></div>` : `<div>Current: <strong>${formatPA(value)} pA</strong></div>`;
  tooltip.innerHTML = `<div>Time: <strong>${formatElapsed(index / SAMPLE_RATE, 4)}</strong></div><div>Sample: ${intFmt.format(index)}</div>${label}`;
  tooltip.hidden = false;
  const left = clamp(pos.x + 14, 3, dimensions.width - 186);
  const top = clamp(pos.y - 74, 0, dimensions.height - 85);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function updateStatistics() {
  $('currentValue').textContent = formatPA(stream.latestPA);
  $('baselineValue').textContent = formatPA(stream.detector.baseline);
  $('eventValue').textContent = intFmt.format(stream.detector.total);
  const cutoff = stream.history.nextIndex - SAMPLE_RATE;
  const perSecond = stream.detector.events.reduce((acc, ev) => acc + (ev.startSample >= cutoff ? 1 : 0), 0);
  $('rateValue').textContent = perSecond.toFixed(1);
  $('throughputValue').textContent = stream.packets ? throughput.toFixed(1) : '—';
  $('bufferValue').textContent = (stream.history.availableSamples / SAMPLE_RATE).toFixed(1);
  if (!stream.detector.events.length) {
    $('eventRows').innerHTML = '<tr><td colspan="6" class="table-empty">No events detected yet. Waiting for samples…</td></tr>';
    return;
  }
  const rows = stream.detector.events.slice(-7).reverse();
  const frag = document.createDocumentFragment();
  for (let i = 0; i < rows.length; i++) {
    const ev = rows[i];
    const tr = document.createElement('tr');
    tr.className = 'event-row'; tr.tabIndex = 0;
    const eventNum = stream.detector.total - i;
    tr.innerHTML = `<td>#${intFmt.format(eventNum)}</td><td>${(ev.startSample / SAMPLE_RATE).toFixed(4)} s</td><td>${ev.depthPA.toFixed(1)} pA</td><td>${(ev.durationSamples * 10).toFixed(0)} µs (${ev.durationSamples})</td><td>${ev.minPA.toFixed(1)} pA</td><td class="inspect-arrow">↗</td>`;
    const jump = () => inspectEvent(ev);
    tr.addEventListener('click', jump);
    tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); jump(); } });
    frag.append(tr);
  }
  $('eventRows').replaceChildren(frag);
}

function inspectEvent(ev) {
  if (ev.startSample < stream.history.oldestIndex) return;
  setWindow(.001);
  followLive = false;
  $('followCheck').checked = false;
  viewportEnd = ev.startSample + 52;
  selectedEvent = ev.startSample;
  dirty = true;
}

function resize() {
  const bounds = area.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const width = Math.round(bounds.width), height = Math.round(bounds.height);
  if (width < 1 || height < 1) return;
  if (dimensions.width !== width || dimensions.height !== height || dimensions.dpr !== dpr) {
    dimensions = { width, height, dpr };
    plot.width = Math.round(width * dpr);
    plot.height = Math.round(height * dpr);
    dirty = true;
  }
}
new ResizeObserver(resize).observe(area);
window.addEventListener('resize', resize);

plot.addEventListener('pointermove', e => {
  const rect = plot.getBoundingClientRect();
  pointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  if (dragging) {
    const deltaPixels = pointer.x - dragging.x;
    followLive = false; $('followCheck').checked = false;
    viewportEnd = dragging.end - deltaPixels / getBox().w * windowSamples();
    selectedEvent = null;
  }
  dirty = true;
});
plot.addEventListener('pointerleave', () => { if (!dragging) pointer = null; dirty = true; });
plot.addEventListener('pointerdown', e => {
  if (e.button !== 0 || !stream.history.availableSamples) return;
  const rect = plot.getBoundingClientRect();
  dragging = { x: e.clientX - rect.left, end: getView().end };
  plot.setPointerCapture(e.pointerId);
});
plot.addEventListener('pointerup', () => { dragging = null; dirty = true; });
plot.addEventListener('pointercancel', () => { dragging = null; pointer = null; dirty = true; });
plot.addEventListener('wheel', e => {
  if (!stream.history.availableSamples) return;
  e.preventDefault();
  const rect = plot.getBoundingClientRect();
  const posX = e.clientX - rect.left;
  const box = getBox();
  const fraction = clamp((posX - box.x) / box.w, 0, 1);
  setWindow(windowSeconds * (e.deltaY < 0 ? 0.78 : 1.28), true, fraction);
}, { passive: false });
plot.addEventListener('dblclick', goLive);

$('connectBtn').addEventListener('click', connectWebSocket);
$('disconnectBtn').addEventListener('click', () => { stopSource(); updateStatistics(); });
$('demoBtn').addEventListener('click', startDemo);
$('emptyDemoBtn').addEventListener('click', startDemo);
$('windowSelect').addEventListener('change', e => setWindow(Number(e.target.value)));
$('followCheck').addEventListener('change', e => { const currentEnd = getView().end; followLive = e.target.checked; if (!followLive) viewportEnd = currentEnd; selectedEvent = null; dirty = true; });
$('autoscaleCheck').addEventListener('change', e => { autoScale = e.target.checked; fixedYRange = null; dirty = true; });
$('markersCheck').addEventListener('change', e => { showMarkers = e.target.checked; dirty = true; });
$('thresholdInput').addEventListener('input', e => {
  const threshold = Number(e.target.value);
  $('thresholdValue').textContent = threshold;
  stream.thresholdPA = threshold;
  stream.detector.thresholdPA = threshold;
  stream.detector.resetTransient();
});
$('liveBtn').addEventListener('click', goLive);
$('zoomInBtn').addEventListener('click', () => setWindow(windowSeconds / 2, !followLive, .5));
$('zoomOutBtn').addEventListener('click', () => setWindow(windowSeconds * 2, !followLive, .5));
$('snapshotBtn').addEventListener('click', () => {
  plot.toBlob(blob => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `mr1-waveform-${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
    a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, 'image/png');
});
window.addEventListener('keydown', e => {
  if (['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)) return;
  if (e.key.toLowerCase() === 'l') goLive();
  else if (e.key === '+') setWindow(windowSeconds / 2, !followLive, .5);
  else if (e.key === '-') setWindow(windowSeconds * 2, !followLive, .5);
});

setInterval(() => {
  throughput = samplesThisSecond / 1000;
  samplesThisSecond = 0;
  updateStatistics();
  if (state === 'connected' && stream.packets > 0 && performance.now() - lastPacketAt > 2500) {
    $('connectionHelp').textContent = 'Connected, but no samples received for 2.5 seconds. Check the bridge stream.';
  }
}, 1000);
setInterval(updateStatistics, 300);

function frame(time) {
  if (dirty && time - lastPaint > 40) {
    drawCanvas();
    dirty = false;
    lastPaint = time;
  }
  requestAnimationFrame(frame);
}
resize();
setStatus('offline');
updateStatistics();
requestAnimationFrame(frame);

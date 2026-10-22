/*
 * Copyright (C) 2026 Lawrence R. Kincheloe III / Molecular Reality Corp
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * @file web_ui_assets.h
 * @brief Embedded HTML5/Canvas Oscilloscope and Control Dashboard in PROGMEM
 */

#pragma once

#include <Arduino.h>

static const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MR1 Nanopore Reader</title>
<style>
  :root {
    --bg: #0f141c;
    --panel: #1a2230;
    --border: #2d384e;
    --text: #e2e8f0;
    --accent: #38bdf8;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #eab308;
    --grid: #1e293b;
    --trace: #00ffaa;
  }
  body {
    margin: 0; padding: 16px;
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  header {
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 2px solid var(--border); padding-bottom: 12px; margin-bottom: 16px;
  }
  h1 { margin: 0; font-size: 1.4rem; color: var(--accent); }
  .badges { display: flex; gap: 8px; }
  .badge {
    padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
    background: var(--panel); border: 1px solid var(--border);
  }
  .badge.ok { background: #064e3b; color: #6ee7b7; border-color: var(--green); }
  .badge.alert { background: #7f1d1d; color: #fca5a5; border-color: var(--red); animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  .layout { display: grid; grid-template-columns: 1fr 340px; gap: 16px; }
  .scope-box {
    background: #05080f; border: 1px solid var(--border); border-radius: 8px;
    padding: 12px; display: flex; flex-direction: column; align-items: center;
  }
  canvas {
    background: #000; border: 1px solid #1e293b; border-radius: 4px;
    width: 100%; height: 380px;
  }
  .controls-sidebar { display: flex; flex-direction: column; gap: 16px; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px;
  }
  .card h3 { margin: 0 0 10px 0; font-size: 0.95rem; color: var(--accent); }
  .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  label { font-size: 0.8rem; color: #94a3b8; }
  input[type="range"] { width: 100%; accent-color: var(--accent); margin: 6px 0; }
  input[type="number"] {
    background: #0f172a; border: 1px solid var(--border); color: var(--text);
    padding: 4px 8px; border-radius: 4px; width: 80px; text-align: right;
  }
  button {
    background: var(--accent); color: #000; border: none; padding: 8px 12px;
    border-radius: 4px; font-weight: bold; cursor: pointer; transition: 0.2s;
  }
  button:hover { opacity: 0.9; }
  button.estop { background: var(--red); color: #fff; width: 100%; padding: 12px; font-size: 1rem; }
  button.secondary { background: #334155; color: var(--text); }
  .stat { font-family: monospace; font-size: 0.85rem; color: #38bdf8; }
</style>
</head>
<body>
<header>
  <div>
    <h1>MR1 Nanopore Reader</h1>
    <small style="color:#64748b">ESP32-S3 + AD40xx (100 kSPS) + MCP4822</small>
  </div>
  <div class="badges">
    <div id="badge-leak" class="badge ok">LEAK: OK</div>
    <div id="badge-pump" class="badge">PUMP: OFFLINE</div>
    <div id="badge-stream" class="badge">STREAM: IDLE</div>
  </div>
</header>

<div class="layout">
  <div class="scope-box">
    <canvas id="scopeCanvas" width="800" height="380"></canvas>
    <div style="display:flex; justify-content:space-between; width:100%; margin-top:8px;">
      <span class="stat" id="stat-rate">Rate: 100 kHz</span>
      <span class="stat" id="stat-vbias">Bias: 0.0 mV</span>
      <span class="stat" id="stat-rms">RMS: -- pA</span>
    </div>
  </div>

  <div class="controls-sidebar">
    <div class="card">
      <h3>Pore Bias Voltage (Ignition)</h3>
      <div class="row">
        <label>Voltage (-1587 to +1587 mV):</label>
        <span class="stat" id="val-bias">0.0 mV</span>
      </div>
      <input type="range" id="slider-bias" min="-1587" max="1587" step="1" value="0">
      <div style="display:flex; gap:8px; margin-top:8px;">
        <button id="btn-zero" class="secondary" style="flex:1">Zero Bias</button>
        <button id="btn-pulse" style="flex:1">Pulse (+1.2V)</button>
      </div>
    </div>

    <div class="card">
      <h3>Peristaltic Pump Control (J22)</h3>
      <div class="row">
        <label>Flow / RPM:</label>
        <input type="number" id="pump-rpm" min="0" max="300" value="60">
      </div>
      <div style="display:flex; gap:8px; margin-bottom:12px;">
        <button id="btn-pump-fwd" style="flex:1">Fwd</button>
        <button id="btn-pump-rev" class="secondary" style="flex:1">Rev</button>
        <button id="btn-pump-stop" class="secondary" style="flex:1">Stop</button>
      </div>
      <button id="btn-estop" class="estop">EMERGENCY CUTOFF</button>
    </div>

    <div class="card">
      <h3>Safety & Diagnostics</h3>
      <div class="row">
        <label>Moat Leak Sensor:</label>
        <span id="stat-leak-text" class="stat">NORMAL</span>
      </div>
      <button id="btn-reset-leak" class="secondary" style="width:100%; margin-top:4px;">Reset Leak Latch</button>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('scopeCanvas');
const ctx = canvas.getContext('2d');
let points = [];
const maxPoints = 500;

function drawScope() {
  ctx.fillStyle = '#05080f';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Graticule Grid
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 50) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 38) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }

  // Center line
  ctx.strokeStyle = '#334155';
  ctx.beginPath(); ctx.moveTo(0, canvas.height/2); ctx.lineTo(canvas.width, canvas.height/2); ctx.stroke();

  // Waveform trace
  if (points.length > 1) {
    ctx.strokeStyle = '#00ffaa';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const dx = canvas.width / maxPoints;
    for (let i = 0; i < points.length; i++) {
      const x = i * dx;
      const y = canvas.height/2 - (points[i] / 32768.0) * (canvas.height/2 - 10);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  requestAnimationFrame(drawScope);
}
drawScope();

// WebSocket connection for real-time visualization & telemetry
const ws = new WebSocket(`ws://${location.host}/ws`);
ws.onmessage = (event) => {
  if (event.data.startsWith('{')) {
    const s = JSON.parse(event.data);
    document.getElementById('stat-vbias').innerText = `${s.bias_mv.toFixed(1)} mV`;
    document.getElementById('badge-pump').className = s.pump_run ? 'badge ok' : 'badge';
    document.getElementById('badge-pump').innerText = s.pump_run ? `PUMP: ${s.pump_rpm} RPM` : (s.pump_conn ? 'PUMP: STOPPED' : 'PUMP: OFFLINE');
    document.getElementById('badge-leak').className = s.leak ? 'badge alert' : 'badge ok';
    document.getElementById('badge-leak').innerText = s.leak ? 'LEAK DETECTED' : 'LEAK: OK';
    document.getElementById('stat-leak-text').innerText = s.leak ? 'ALERT (TRIPPED)' : 'NORMAL';
    document.getElementById('badge-stream').className = s.streaming ? 'badge ok' : 'badge';
    document.getElementById('badge-stream').innerText = s.streaming ? 'STREAMING 100k' : 'IDLE';
  } else {
    // Decimated sample points
    const val = parseInt(event.data);
    points.push(val);
    if (points.length > maxPoints) points.shift();
  }
};

// UI Handlers
const slider = document.getElementById('slider-bias');
const biasVal = document.getElementById('val-bias');
slider.oninput = () => {
  biasVal.innerText = `${slider.value} mV`;
};
slider.onchange = () => {
  fetch('/api/bias', { method: 'POST', body: slider.value });
};
document.getElementById('btn-zero').onclick = () => {
  slider.value = 0; biasVal.innerText = '0 mV';
  fetch('/api/bias', { method: 'POST', body: '0' });
};
document.getElementById('btn-pulse').onclick = () => {
  fetch('/api/pulse', { method: 'POST', body: '1200' });
};
document.getElementById('btn-pump-fwd').onclick = () => {
  fetch('/api/pump', { method: 'POST', body: JSON.stringify({ cmd: 'fwd', rpm: document.getElementById('pump-rpm').value }) });
};
document.getElementById('btn-pump-rev').onclick = () => {
  fetch('/api/pump', { method: 'POST', body: JSON.stringify({ cmd: 'rev', rpm: document.getElementById('pump-rpm').value }) });
};
document.getElementById('btn-pump-stop').onclick = () => {
  fetch('/api/pump', { method: 'POST', body: JSON.stringify({ cmd: 'stop' }) });
};
document.getElementById('btn-estop').onclick = () => {
  fetch('/api/pump', { method: 'POST', body: JSON.stringify({ cmd: 'estop' }) });
};
document.getElementById('btn-reset-leak').onclick = () => {
  fetch('/api/leak/reset', { method: 'POST' });
};
</script>
</body>
</html>
)rawliteral";

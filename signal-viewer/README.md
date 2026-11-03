# MR1 Signal Viewer

A browser-based, single-channel solid-state nanopore current visualiser for the [MR1 WebSocket bridge](https://github.com/LokiMetaSmith/MR1/blob/main/scripts/websocket_bridge.py). **No npm packages or build step are required.**

## Run it

1. From the **MR1 repository**, launch the existing simulator/bridge:

   ```bash
   pip install 'websockets>=12.0'
   python scripts/websocket_bridge.py --mock
   ```

   The bridge defaults to `ws://localhost:8765`. If you're on another machine, bind it to an accessible interface with `--host 0.0.0.0` and enter that machine's address in the viewer. Do not expose an unauthenticated bridge to the public internet.

2. In the **mr1-signal-viewer** directory, start a local static web server:

   ```bash
   python3 -m http.server 8000
   ```

3. Visit <http://localhost:8000>, leave `ws://localhost:8765` selected, and click **Connect to bridge**. Or click **Run local demo** without starting Python's bridge; it generates and parses the same wire format in-browser.

   When serving from an HTTPS page, browsers generally require a `wss://` endpoint (or a local dev HTTP page).

## Important detail about the MR1 mock

As of the inspected source, `scripts/daq_client.py` currently creates **25-sample** simulated blockades, despite the proposed 2-sample events. For a 20 µs / 2-sample simulation, change this line in `MockSerialPort._generate_mock_stream()`:

```python
self._event_samples_remaining = 25  # ~250 us blockade
```

to:

```python
self._event_samples_remaining = 2  # 20 us at 100 kHz
```

The visualizer works with both event durations. The **local demo** already creates two-sample events.

## Exact WebSocket protocol

The bridge builds frames using Python `struct.pack(f'<Q{len(samples_pa)}f', timestamp_us, *samples_pa)`:

- Bytes `0..7`: **uint64 little-endian** timestamp in microseconds (time of the first sample in the frame).
- Bytes `8..end`: zero or more **float32 little-endian** samples, already converted to **pA**.
- Nominal rate: **100,000 samples/second**, i.e. 10 µs/sample.
- MR1 DAQ mock sends **64 samples per frame**, but the viewer does not hardcode the packet size.
- Underlying DAQ has a uint32 µs timestamp. The decoder handles the ~71-minute rollover, dropped frames, and out-of-order frames. Gaps are rendered as missing samples rather than joining unrelated times.
- The bridge currently does not support browser control commands; the UI therefore does not invent acquisition controls.

## Features

- 60-second Float32 rolling buffer (24 MB of raw data at 100 kHz).
- Multiresolution min/max summaries (16 / 256 / 4096 sample blocks), keeping 2-sample dips visible in overview mode.
- Direct vertical min/max rendering when zoomed out; original waveform + sample points when zoomed in.
- Live scrolling, pause-follow without stopping acquisition, scroll-to-zoom, drag-to-pan, double-click to return live, event-row navigation, PNG snapshots.
- Optional threshold-based raw-sample event detection with a gated adaptive EMA baseline. This heuristic is not a validated physical event detector and its output depends on the threshold/noise; changing the threshold applies only to future samples.
- Event register with peak blockade depth, measured duration, minimum current, and sampling-time positions.

## Tests

```bash
node --test tests/*.test.mjs
```

The app uses modern browser features (`DataView.getBigUint64`, `ResizeObserver`, ES modules, Canvas 2D), supported in recent Chrome, Firefox, and Safari.

## Project files

- `index.html` – UI markup.
- `styles.css` – responsive dark interface.
- `src/app.js` – WebSocket connection, live demo, interaction, Canvas renderer.
- `src/signal.js` – exact binary decoder, rolling summaries, simple event detector.
- `tests/signal.test.mjs` – Node regression tests.

## Signal analysis caveat

A min/max pixel range preserves **extremes**, not the exact number, order, or duration of events in that pixel. The optional event detector operates on raw samples before any decimation. The baseline line is the **latest** estimate, not a reconstructed historical baseline trace.

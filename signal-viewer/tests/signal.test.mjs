import test from 'node:test';
import assert from 'node:assert/strict';
import { SignalHistory, EventDetector, MR1Stream, makeMR1Frame } from '../src/signal.js';

test('binary little endian protocol decodes bridge timestamp and float32 pA', () => {
  const stream = new MR1Stream({ sampleRate: 100000, bufferSeconds: 1 });
  const packet = makeMR1Frame(1234567890123n, [120.5, -44.25, 99.125]);
  stream.ingestPacket(packet);
  assert.equal(stream.lastTimestampUs, 1234567890123n);
  assert.equal(stream.history.get(0), 120.5);
  assert.equal(stream.history.get(1), -44.25);
  assert.equal(stream.received, 3);
});

test('timestamp gaps are represented by missing samples', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  stream.ingestPacket(makeMR1Frame(0n, [1, 2, 3, 4]));
  stream.ingestPacket(makeMR1Frame(60n, [9, 10]));
  assert.equal(stream.history.nextIndex, 8);
  assert.ok(Number.isNaN(stream.history.get(4)));
  assert.ok(Number.isNaN(stream.history.get(5)));
  assert.equal(stream.history.get(6), 9);
  assert.equal(stream.lost, 2);
});

test('32-bit microsecond timestamp rollover survives the bridge', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  stream.ingestPacket(makeMR1Frame(4294967276n, [5, 6]));
  stream.ingestPacket(makeMR1Frame(0n, [7, 8]));
  assert.equal(stream.received, 4);
  assert.equal(stream.history.nextIndex, 4);
});

test('min max summaries retain 2 sample events at far zoom and wrap correctly', () => {
  const history = new SignalHistory(100, 1);
  for (let i = 0; i < 100; i++) history.append(i === 29 || i === 30 ? 60 : 100);
  assert.deepEqual(history.range(0, 100), { min: 60, max: 100 });
  assert.deepEqual(history.range(28, 31), { min: 60, max: 100 });
  for (let i = 0; i < 100; i++) history.append(110);
  assert.equal(history.oldestIndex, 100);
  assert.deepEqual(history.range(100, 200), { min: 110, max: 110 });
  assert.ok(Number.isNaN(history.get(30)));
});

test('event detector records exactly 2-sample downward blockades', () => {
  const detector = new EventDetector(20, 2);
  for (let i = 0; i < 100; i++) detector.ingest(120, i);
  detector.ingest(89, 100);
  detector.ingest(90, 101);
  const event = detector.ingest(120, 102);
  assert.equal(event.startSample, 100);
  assert.equal(event.durationSamples, 2);
  assert.equal(detector.total, 1);
});

test('malformed and overlapping frames are rejected or ignored', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  assert.throws(() => stream.ingestPacket(new ArrayBuffer(9)), /Expected/);
  stream.ingestPacket(makeMR1Frame(100n, [1, 2, 3]));
  assert.equal(stream.ingestPacket(makeMR1Frame(110n, [3, 4])).ignored, true);
  assert.equal(stream.history.nextIndex, 3);
});

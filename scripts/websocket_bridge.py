import daq_client
import struct
import time
from threading import Thread
from websockets.sync.server import serve

_ws = None
_server = None

def handle_client(websocket):
    global _ws
    _ws = websocket
    for message in websocket:
        print(message)
    print("Closing WebSocket")


def run_websocket():
    global _server
    with serve(handle_client, "localhost", 8765) as server:
        _server = server
        server.serve_forever()

def get_binary_frame_chunk(timestamp_us, samples):
    '''From the docs:
    
    Binary Frame Chunk (Sent @ 100 Hz, 1000 samples per message):

    Header: 8-byte microsecond timestamp.
    Body: Array of float32 current values in picoamperes ( 1000 × 4  bytes = 4000  bytes ).
    '''
    #timestamp_us = time.time_ns()//1000
    
    samples_pa = [s * 10**-12 for s in samples]
    
    format_string = "<Q" + "f" * len(samples)
    
    data = [timestamp_us] + samples_pa
    ret = struct.pack(format_string, *data)
    
    return ret    

def listen_to_mr1(duration_sec):
    global _ws

    client = daq_client.DaqClient(port = "blah", is_mock = True)
    client.connect()
    client.start_streaming()
    
    print("\n" + "=" * 70)
    print("  MR1 Nanopore 100 kHz WebSocket Bridge (Active)")
    print("  Press Ctrl+C to stop acquisition.")
    print("=" * 70)

    start = time.time()
    try:
        while client.is_running:
            if duration_sec and (time.time() - start) >= duration_sec:
                break

            latest_frame = client.frame_queue.get()
            if latest_frame:
                currents = [daq_client.raw_to_current(s, client.vref, client.gain_ohms) for s in latest_frame.samples]
                print(f"Frame received, number of samples: {len(currents)}")
                
                timestamp_us = latest_frame.timestamp_us
                print(f"timestamp from frame: {timestamp_us}")
                bfc = get_binary_frame_chunk(timestamp_us, currents)
                
                if _ws:
                    _ws.send(bfc)
                
    except KeyboardInterrupt:
        print("\n\nUser interrupted acquisition.")
    finally:
        client.stop_streaming()
        print("\n" + "=" * 70)

if __name__ == "__main__":
    t = Thread(target=run_websocket)
    t.start()
    listen_to_mr1(120)
    _server.shutdown()
    t.join()


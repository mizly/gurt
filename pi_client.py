import asyncio
import websockets
import cv2
import numpy as np
import time
import struct
import ssl
import subprocess
import os
import sys
import serial

# Configuration
SERVER_URL = "ws://10.167.168.92:8000/ws/pi"
# SERVER_URL = "wss://uottahack-8-327580bc1291.herokuapp.com/ws/pi"

SERIAL_PORT = "/dev/ser1"
BAUD_RATE = 115200

# Camera Commands to try for QNX fallback
# We prioritize the custom streamer which dumps raw RGBA
QNX_COMMANDS = [
    ["./camera_streamer"], 
    ["./camera_example3_viewfinder"]
]

# State for throttling
latest_control_data = None
current_ser = None

async def serial_transmitter():
    global latest_control_data, current_ser
    last_sent_data = None
    print("Serial transmitter task started.")
    
    try:
        while True:
            if current_ser and current_ser.is_open:
                # Send controls
                if latest_control_data and latest_control_data != last_sent_data:
                    try:
                        def write_and_flush(data):
                            current_ser.write(data)
                            current_ser.flush()
                        await asyncio.to_thread(write_and_flush, latest_control_data)
                        last_sent_data = latest_control_data
                    except Exception as e:
                        print(f"Serial write error: {e}")
            
            # Run at ~50Hz (20ms)
            await asyncio.sleep(0.02)
    except asyncio.CancelledError:
        print("Serial transmitter task stopping...")

async def receive_controls(websocket):
    global latest_control_data, current_ser
    print("Listening for controls...")
    
    try:
        # Open serial with settings to prevent Arduino auto-reset
        current_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
        current_ser.setDTR(False) 
        print(f"Serial port {SERIAL_PORT} opened. Waiting for Arduino boot...")
        await asyncio.sleep(1.5) # Allow Arduino to initialize
        current_ser.reset_input_buffer()
        current_ser.reset_output_buffer()
        print("Serial ready.")
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        current_ser = None

    last_print_time = 0
    try:
        while True:
            data = await websocket.recv()
            if isinstance(data, bytes) and len(data) == 8:
                # 1. Unpack browser data (Unsigned 8 bytes)
                # Browser format: [UX, UY, RX, RY, LT, RT, B_LOW, B_HIGH]
                u_lx, u_ly, u_rx, u_ry, u_lt, u_rt = data[:6]
                raw_btns = int.from_bytes(data[6:], byteorder='little')
                
                # 2. Scale to Signed (-127 to 127) and Constrain
                # Browser is 0-255, we want -127 to 127
                def scale(val):
                    return max(-127, min(127, val - 127))

                lx = scale(u_lx)
                ly = scale(u_ly)
                rx = scale(u_rx)
                ry = scale(u_ry)
                lt = scale(u_lt)
                rt = scale(u_rt)
                
                # 3. Re-pack in Big Endian Signed format (>bbbbbbH)
                new_packet = struct.pack(">bbbbbbH", lx, ly, rx, ry, lt, rt, raw_btns)
                
                # Update global state for transmitter task
                latest_control_data = new_packet
                
                # Throttle printing to 10Hz
                current_time = time.time()
                if current_time - last_print_time > 0.1:
                    print(f"\rMapped: L({lx:4},{ly:4}) R({rx:4},{ry:4}) T({lt:4},{rt:4}) B:{raw_btns:016b}   ", end="", flush=True)
                    last_print_time = current_time

    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed (Receive)")
    except Exception as e:
        print(f"\nError in receive_controls: {e}")
    finally:
        if current_ser:
            current_ser.close()

async def send_video(websocket):
    print("Starting Video Stream Initialization...")
    
    # --- METHOD 1: OpenCV Standard ---
    cap = cv2.VideoCapture(0)
    # Check if opened successfully
    if cap.isOpened():
        print("-> Using OpenCV Camera (Method 1)")
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("OpenCV stream ended.")
                    break
                
                # Resize if needed to 640x480 to match everything else
                if frame.shape[1] != 640 or frame.shape[0] != 480:
                    frame = cv2.resize(frame, (640, 480))

                # Compress to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                
                # Timestamp (ms, double)
                timestamp = time.time() * 1000
                packed_time = struct.pack('<d', timestamp)
                
                await websocket.send(packed_time + buffer.tobytes())
                await asyncio.sleep(0.001) # Yield slightly
        except Exception as e:
            print(f"OpenCV Error: {e}")
        finally:
            cap.release()
            print("OpenCV released. Attempting fallback...")
    else:
        print("-> OpenCV capture failed to open.")

    # --- METHOD 2: QNX Native Subprocess (SKIPPED for debugging) ---
    print("-> Skipping Method 2 as requested.")
    # (Method 2 logic removed to go directly to noise)

    # --- METHOD 3: Generated Noise ---
    print("-> All methods failed. Streaming Noise (Method 3)")
    try:
        while True:
            # Generate random noise
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            # Add Overlay
            cv2.putText(frame, "NO SIGNAL", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            current_time = f"{time.time():.1f}"
            cv2.putText(frame, current_time, (50, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            timestamp = time.time() * 1000
            packed_time = struct.pack('<d', timestamp)
            await websocket.send(packed_time + buffer.tobytes())
            
            # Limit to ~30 FPS
            await asyncio.sleep(0.033) 
    except Exception as e:
        print(f"Noise Gen Error: {e}")

async def main():
    print(f"Connecting to {SERVER_URL}...")
    
    ssl_context = None
    if SERVER_URL.startswith("wss"):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations("cacert.pem")
    
    async with websockets.connect(SERVER_URL, ssl=ssl_context) as websocket:
        print("Connected!")
        await asyncio.gather(
            receive_controls(websocket),
            send_video(websocket),
            serial_transmitter()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")

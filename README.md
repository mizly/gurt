# UOttaHack 8 Project

This project implements a real-time remote control system with video streaming using WebSockets. It consists of a central FastAPI server, a web-based client for control, and a Python client (simulating a Raspberry Pi) that receives controls and streams video.

## Prerequisites

- Python 3.8+
- Webcam (optional, for video streaming)

## Setup

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd uottahack-8
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Project

You will need two terminal windows running.

### 1. Start the Server

This starts the central communication hub.

```bash
python server.py
```

You should see:
> Server starting. Access the web interface at: http://localhost:8000

Open your browser and navigate to [http://localhost:8000](http://localhost:8000) to see the control interface.

### 2. Start the Pi Client

This code is intended to run on the **Raspberry Pi** (the robot), but you can run it on the **same laptop** as the server for testing purposes. It connects to the server, receives control commands, and streams video (from your webcam or generated noise).

```bash
python pi_client.py
```

## Usage

1.  Ensure both the **Server** and **Pi Client** are running.
2.  Open the web interface ([http://localhost:8000](http://localhost:8000)).
3.  The web interface sends control data (simulated or from a gamepad) to the server.
4.  The server relays these controls to the `pi_client.py`.
5.  The `pi_client.py` prints the received controls and streams video frames back to the server.
6.  The web interface displays the video stream.

## Troubleshooting

-   **Port 8000 already in use**: Edit `server.py` and change the port in `uvicorn.run(..., port=8000)`.
-   **No Webcam**: The `pi_client.py` will automatically fall back to generating visual noise if no webcam is detected.
-   **Connection Refused**: Ensure the server is running before starting the client.
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.connection import ConnectionManager
from backend.solana import HOUSE_KEYPAIR, solana_client # Needed for /house-key route

app = FastAPI()

manager = ConnectionManager()

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return FileResponse("static/index.html")

@app.get("/house-key")
async def get_house_key():
    # Print balance for debug
    try:
        balance = await solana_client.get_balance(HOUSE_KEYPAIR.pubkey())
        print(f"[DEBUG] Current House Balance: {balance.value / 10**9} SOL")
    except:
        pass
    return {"publicKey": str(HOUSE_KEYPAIR.pubkey())}

@app.websocket("/ws/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    await manager.connect(websocket, client_type)
    try:
        while True:
            # We receive the raw message dictionary (bytes or text)
            message = await websocket.receive()
            
            if client_type == "client":
                await manager.process_client_message(websocket, message)
            elif client_type == "pi":
                await manager.process_pi_message(websocket, message)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
    except Exception as e:
        print(f"Error in {client_type}: {e}")
        # Ensure cleanup if loop crashes
        if websocket.client_state.name == "CONNECTED":
             await websocket.close()

if __name__ == "__main__":
    print("Server starting. Access at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

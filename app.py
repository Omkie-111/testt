from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Serve verification file statically
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

# Store connected clients
connected_clients = set()

@app.get("/", response_class=HTMLResponse)
async def get_transcript():
    """Serve the HTML page on the root endpoint."""
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/.well-known/pki-validation/4E1F5DA990AE45630EE32486534FB035.txt")
async def serve_auth_file():
    """Serve the SSL verification file."""
    return FileResponse(".well-known/pki-validation/4E1F5DA990AE45630EE32486534FB035.txt")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for frontend clients to receive real-time transcriptions."""
    await websocket.accept()
    connected_clients.add(websocket)
    print("New frontend client connected")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")

            # **Don't send the message back to sender (db.py script)**

            # **Broadcast transcription to all connected frontend clients**
            for client in connected_clients:
                if client != websocket:  # Ensure we don't send back to sender
                    await client.send_text(data)

    except WebSocketDisconnect:
        print("Frontend client disconnected")
        connected_clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)

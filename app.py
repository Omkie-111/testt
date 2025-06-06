# # from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# # from fastapi.responses import HTMLResponse, FileResponse
# # from fastapi.middleware.cors import CORSMiddleware
# # from fastapi.staticfiles import StaticFiles
# # import uvicorn
# # import asyncio

# # app = FastAPI()

# # # Allow CORS
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # Serve static files
# # app.mount("/static", StaticFiles(directory="static"), name="static")
# # # Serve verification file statically
# # # app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

# # # Store connected clients
# # connected_clients = set()

# # @app.get("/", response_class=HTMLResponse)
# # async def get_transcript():
# #     """Serve the HTML page on the root endpoint."""
# #     with open("static/index.html") as f:
# #         return HTMLResponse(content=f.read())
    
# # # @app.get("/.well-known/pki-validation/4E1F5DA990AE45630EE32486534FB035.txt")
# # # async def serve_auth_file():
# # #     """Serve the SSL verification file."""
# # #     return FileResponse(".well-known/pki-validation/4E1F5DA990AE45630EE32486534FB035.txt")

# # # @app.websocket("/ws")
# # # async def websocket_endpoint(websocket: WebSocket):
# # #     """WebSocket endpoint for frontend clients to receive real-time transcriptions."""
# # #     await websocket.accept()
# # #     connected_clients.add(websocket)
# # #     print("New frontend client connected")

# # #     try:
# # #         while True:
# # #             data = await websocket.receive_text()
# # #             print(f"Received message: {data}")

# # #             # **Don't send the message back to sender (db.py script)**

# # #             # **Broadcast transcription to all connected frontend clients**
# # #             for client in connected_clients:
# # #                 if client != websocket:  # Ensure we don't send back to sender
# # #                     await client.send_text(data)

# # #     except WebSocketDisconnect:
# # #         print("Frontend client disconnected")
# # #         connected_clients.remove(websocket)

# # @app.websocket("/ws")
# # async def websocket_endpoint(websocket: WebSocket):
# #     """WebSocket endpoint for frontend clients to receive real-time transcriptions."""
# #     await websocket.accept()
# #     connected_clients.add(websocket)
# #     print("New frontend client connected")

# #     try:
# #         while True:
# #             message = await websocket.receive()

# #             # Handle text messages
# #             if "text" in message:
# #                 text_data = message["text"]
# #                 print(f"Received text message: {text_data}")

# #                 # Broadcast to all other clients
# #                 for client in connected_clients:
# #                     if client != websocket:
# #                         await client.send_text(text_data)

# #             # Handle binary (audio) messages
# #             elif "bytes" in message:
# #                 bytes_data = message["bytes"]
# #                 print(f"Received binary audio data: {len(bytes_data)} bytes")

# #                 # (Optional) broadcast audio to other clients
# #                 # for client in connected_clients:
# #                 #     if client != websocket:
# #                 #         await client.send_bytes(bytes_data)

# #     except WebSocketDisconnect:
# #         print("Frontend client disconnected")
# #         connected_clients.remove(websocket)

# # if __name__ == "__main__":
# #     uvicorn.run(app, host="0.0.0.0", port=8000)


# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.responses import HTMLResponse, FileResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# import uvicorn
# import os
# import uuid

# app = FastAPI()

# # CORS setup
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static file hosting
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # In-memory client tracking
# connected_clients = set()

# # Constants
# TRANSCRIPT_DIR = "transcripts"
# os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
# CHUNK_DURATION_SECONDS = 120  # 2 minutes
# BYTES_PER_SECOND = 32000      # Adjust based on your actual audio bitrate

# @app.get("/", response_class=HTMLResponse)
# async def get_transcript():
#     """Serve the frontend HTML page."""
#     with open("static/index.html") as f:
#         return HTMLResponse(content=f.read())

# @app.get("/download/{filename}")
# async def download_transcript(filename: str):
#     """Provide a downloadable transcript file."""
#     file_path = os.path.join(TRANSCRIPT_DIR, filename)
#     if os.path.exists(file_path):
#         return FileResponse(file_path, media_type="text/plain", filename=filename)
#     return {"error": "File not found"}

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     """WebSocket endpoint for streaming transcriptions and audio."""
#     await websocket.accept()
#     connected_clients.add(websocket)
#     print("New frontend client connected")

#     transcript_buffer = ""
#     audio_byte_counter = 0
#     chunk_index = 1
#     session_id = str(uuid.uuid4())

#     try:
#         while True:
#             message = await websocket.receive()

#             # Handle text messages (transcripts)
#             if "text" in message:
#                 text_data = message["text"]
#                 print(f"Received text message: {text_data}")
#                 transcript_buffer += text_data.strip() + "\n"

#                 # Broadcast to other clients (not the sender)
#                 for client in connected_clients:
#                     if client != websocket:
#                         await client.send_text(text_data)

#             # Handle binary audio data
#             elif "bytes" in message:
#                 bytes_data = message["bytes"]
#                 audio_byte_counter += len(bytes_data)
#                 print(f"Received binary audio data: {len(bytes_data)} bytes")

#                 # Save transcript every ~2 minutes of audio
#                 if audio_byte_counter >= BYTES_PER_SECOND * CHUNK_DURATION_SECONDS:
#                     filename = f"transcript_{session_id}_{chunk_index}.txt"
#                     filepath = os.path.join(TRANSCRIPT_DIR, filename)

#                     with open(filepath, "w") as f:
#                         f.write(transcript_buffer)

#                     print(f"Saved transcript: {filepath}")

#                     # Notify frontend with a download link
#                     download_link = f"/download/{filename}"
#                     for client in connected_clients:
#                         await client.send_text(f"[Transcript ready] {download_link}")

#                     # Reset for next chunk
#                     transcript_buffer = ""
#                     audio_byte_counter = 0
#                     chunk_index += 1

#     except WebSocketDisconnect:
#         print("Frontend client disconnected")
#         connected_clients.remove(websocket)

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.responses import JSONResponse
# from fastapi.responses import HTMLResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# import uvicorn
# import websockets
# import json
# import os
# import datetime
# import uuid

# app = FastAPI()

# # CORS setup
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static file hosting
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # WebSocket client tracking
# connected_clients = set()

# # Deepgram configuration
# DEEPGRAM_API_KEY = "865b5ebcf07b1b140f283a82b830ba0120c408c3"
# DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"
# DEEPGRAM_PARAMS = {
#     "model": "nova-2",
#     "language": "hi",
#     "punctuate": "true",
#     "smart_format": "true",
#     "diarize": "true",
#     "encoding": "linear16",
#     "sample_rate": 16000
# }

# @app.get("/", response_class=HTMLResponse)
# async def get_index():
#     """Serve the frontend HTML page"""
#     with open("static/index.html") as f:
#         return HTMLResponse(content=f.read())

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     """WebSocket endpoint for streaming transcriptions and audio."""
#     await websocket.accept()
#     connected_clients.add(websocket)
#     print("New frontend client connected")

#     transcript_buffer = ""
#     audio_byte_counter = 0
#     chunk_index = 1
#     session_id = str(uuid.uuid4())

#     try:
#         while True:
#             try:
#                 message = await websocket.receive()

#                 # Handle text messages (transcripts)
#                 if "text" in message:
#                     text_data = message["text"]
#                     print(f"Received text message: {text_data}")
#                     transcript_buffer += text_data.strip() + "\n"

#                     # Broadcast to other clients (not the sender)
#                     for client in connected_clients:
#                         if client != websocket:
#                             await client.send_text(text_data)

#                 # Handle binary audio data
#                 elif "bytes" in message:
#                     bytes_data = message["bytes"]
#                     audio_byte_counter += len(bytes_data)
#                     print(f"Received binary audio data: {len(bytes_data)} bytes")

#                     # Save transcript every ~2 minutes of audio
#                     if audio_byte_counter >= BYTES_PER_SECOND * CHUNK_DURATION_SECONDS:
#                         filename = f"transcript_{session_id}_{chunk_index}.txt"
#                         filepath = os.path.join(TRANSCRIPT_DIR, filename)

#                         with open(filepath, "w") as f:
#                             f.write(transcript_buffer)

#                         print(f"Saved transcript: {filepath}")

#                         # Notify frontend with a download link
#                         download_link = f"/download/{filename}"
#                         for client in connected_clients:
#                             await client.send_text(f"[Transcript ready] {download_link}")

#                         # Reset for next chunk
#                         transcript_buffer = ""
#                         audio_byte_counter = 0
#                         chunk_index += 1

#             except WebSocketDisconnect:
#                 print("Frontend client disconnected inside loop")
#                 if websocket.application_state != WebSocketState.DISCONNECTED:
#                     await websocket.send_json({"status": "Disconnected"})
#                 connected_clients.remove(websocket)
#                 break  # Exit the receive loop

#             except Exception as e:
#                 print(f"Exception in websocket receive loop: {e}")
#                 if websocket.application_state != WebSocketState.DISCONNECTED:
#                     await websocket.send_json({"status": "Disconnected"})
#                 connected_clients.remove(websocket)
#                 break  # Exit the receive loop

#     except Exception as e:
#         print(f"Outer exception in websocket endpoint: {e}")


# @app.get("/report")
# async def get_report():
#     current_time = datetime.datetime.utcnow().isoformat() + "Z"
#     sample_report = {
#         "call_id": "call_12345",
#         "agent_id": "agent_001",
#         "customer_id": "customer_789",
#         "start_time": current_time,
#         "end_time": current_time,
#         "category_reports": {
#             "introduction": {
#                 "title": "Introduction & Setup",
#                 "subcategories": {
#                     "greeting": {
#                         "title": "Executive Greeting & Context Setting",
#                         "entries": [
#                             {
#                                 "timestamp": current_time,
#                                 "value": "Yes",
#                                 "reason": "Proper greeting and context provided.",
#                                 "sentence": [
#                                     "Good morning, this is John from XYZ Corp."
#                                 ],
#                                 "score": 5,
#                                 "nudges": "Greeting\nEnsure you introduce yourself clearly.\nSmile while talking."
#                             }
#                         ],
#                         "final_summary": {
#                             "value": "Yes",
#                             "reason": "Complete greeting done.",
#                             "sentence": [
#                                 "Good morning, this is John from XYZ Corp."
#                             ],
#                             "total_score": 5,
#                             "nudges": "Final Greeting Tips\nMaintain politeness throughout the call."
#                         }
#                     }
#                 },
#                 "final_category_score": 5
#             }
#         },
#         "overall_summary": {
#             "total_score": 5,
#             "max_score": 5,
#             "percentage_score": "100%",
#             "remarks": "Excellent call performance."
#         }
#     }

#     return JSONResponse(content=sample_report)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, RootModel
from typing import Any, Dict, List
import os
import json

app = FastAPI()

report_file = "report.json"
status_file = "status.json"

# Support arbitrary nested structure for report
class ReportModel(RootModel[Dict[str, Any]]):
    pass

# Status model with a single string field
class StatusModel(BaseModel):
    status: str

@app.get("/report")
async def get_report():
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    return JSONResponse(content=report)

@app.post("/report")
async def set_report(report: ReportModel):
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report.root, f, ensure_ascii=False, indent=2)
    return {"message": "Report saved successfully"}

@app.get("/status")
async def get_status():
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Status not found")
    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)
    return JSONResponse(content=status)

@app.post("/status")
async def set_status(status: StatusModel):
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump({"status": status.status}, f, ensure_ascii=False, indent=2)
    return {"message": "Status updated successfully"}


class UserData(BaseModel):
    full_name: str
    status: str
    duration: str
    nudges_observed: int
    nudges_declined: int
    total_score: str

# Static dataset
users_data = [
    UserData(full_name="Babin Kumar", status="Process", duration="600s", nudges_observed=12, nudges_declined=34, total_score="32/100"),
    UserData(full_name="Priya Singh", status="Completed", duration="750s", nudges_observed=20, nudges_declined=15, total_score="75/100"),
    UserData(full_name="Amit Verma", status="On Call", duration="420s", nudges_observed=10, nudges_declined=5, total_score="55/100"),
    UserData(full_name="Sneha Roy", status="Completed", duration="900s", nudges_observed=18, nudges_declined=8, total_score="80/100"),
    UserData(full_name="Rahul Sharma", status="Process", duration="360s", nudges_observed=7, nudges_declined=3, total_score="45/100"),
    UserData(full_name="Meena Gupta", status="Idle", duration="0s", nudges_observed=0, nudges_declined=0, total_score="0/100"),
    UserData(full_name="Ravi Patel", status="On Call", duration="1120s", nudges_observed=22, nudges_declined=12, total_score="72/100"),
    UserData(full_name="Anjali Mehra", status="Completed", duration="810s", nudges_observed=25, nudges_declined=10, total_score="85/100"),
    UserData(full_name="Vikram Yadav", status="Process", duration="560s", nudges_observed=9, nudges_declined=4, total_score="50/100"),
    UserData(full_name="Kajal Pandey", status="Idle", duration="0s", nudges_observed=0, nudges_declined=0, total_score="0/100"),
    UserData(full_name="Suresh Das", status="On Call", duration="670s", nudges_observed=15, nudges_declined=6, total_score="60/100"),
    UserData(full_name="Neha Rani", status="Completed", duration="980s", nudges_observed=30, nudges_declined=9, total_score="90/100"),
    UserData(full_name="Deepak Rana", status="Process", duration="730s", nudges_observed=13, nudges_declined=11, total_score="62/100"),
    UserData(full_name="Divya Joshi", status="Completed", duration="845s", nudges_observed=21, nudges_declined=13, total_score="78/100"),
    UserData(full_name="Nikhil Sinha", status="On Call", duration="610s", nudges_observed=16, nudges_declined=7, total_score="68/100")
]

@app.get("/manager-data", response_model=List[UserData])
def get_user_info():
    return users_data



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

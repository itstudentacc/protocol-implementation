import os
import shutil
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from ConnectionManager import ConnectionManager
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

manager = ConnectionManager()

# Define the directory to store uploaded files
UPLOAD_DIR = Path("files")
UPLOAD_DIR.mkdir(exist_ok=True)

# Max file size: 15 MB
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB in bytes

# Serve files statically from /files
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# @app.websocket("/")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.handler(data, websocket)
#             # await manager.send_personal_message(f"Received:{data}",websocket)

#     except WebSocketDisconnect:
#         manager.disconnect(websocket)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check file size before saving
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        # Define file path
        file_path = UPLOAD_DIR / file.filename
        print(type(file_path))
        # Save the file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return file URL to client
        file_url = f"http://localhost:8001/api/files/{file.filename}"
        response = {
            "body" : file_url
        }
        return response

    except Exception as e:
        # Log error and raise an HTTP exception
        print(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
# Test endpoint to serve files
@app.get("/api/files/{file_name}")
async def serve_file(file_name: str):
    file_path = Path(UPLOAD_DIR) / file_name
    print(file_path)
    if file_path.exists():
        return FileResponse(path=file_path, filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="File not found")
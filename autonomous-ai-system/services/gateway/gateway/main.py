from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import uuid

app = FastAPI(title="Autonomous AI Gateway")

class CreateTaskRequest(BaseModel):
	goal: str
	requirements: Dict[str, Any] = {}

class CreateTaskResponse(BaseModel):
	task_id: str
	status: str

# In-memory realtime store for demo; to be replaced by Redis/Postgres
TASK_STATUS: Dict[str, str] = {}
TASK_EVENTS: Dict[str, asyncio.Queue] = {}

@app.post("/tasks", response_model=CreateTaskResponse)
async def create_task(req: CreateTaskRequest):
	task_id = str(uuid.uuid4())
	TASK_STATUS[task_id] = "planning"
	TASK_EVENTS[task_id] = asyncio.Queue()
	await TASK_EVENTS[task_id].put({"event": "created", "goal": req.goal})
	return CreateTaskResponse(task_id=task_id, status=TASK_STATUS[task_id])

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
	status = TASK_STATUS.get(task_id)
	if status is None:
		return JSONResponse(status_code=404, content={"error": "not found"})
	return {"task_id": task_id, "status": status}

@app.websocket("/ws/tasks/{task_id}")
async def task_ws(ws: WebSocket, task_id: str):
	await ws.accept()
	if task_id not in TASK_EVENTS:
		await ws.send_json({"error": "task not found"})
		await ws.close(code=1008)
		return
	queue = TASK_EVENTS[task_id]
	try:
		await ws.send_json({"event": "subscribed", "task_id": task_id})
		while True:
			event = await queue.get()
			await ws.send_json(event)
	except WebSocketDisconnect:
		return

# Simulated realtime progress loop
async def _simulate_progress(task_id: str):
	await asyncio.sleep(0.5)
	TASK_STATUS[task_id] = "executing"
	await TASK_EVENTS[task_id].put({"event": "status", "status": "executing"})
	await asyncio.sleep(0.5)
	TASK_STATUS[task_id] = "verifying"
	await TASK_EVENTS[task_id].put({"event": "status", "status": "verifying"})
	await asyncio.sleep(0.5)
	TASK_STATUS[task_id] = "publishing"
	await TASK_EVENTS[task_id].put({"event": "status", "status": "publishing"})
	await asyncio.sleep(0.5)
	TASK_STATUS[task_id] = "done"
	await TASK_EVENTS[task_id].put({"event": "status", "status": "done"})

@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str):
	if task_id not in TASK_STATUS:
		return JSONResponse(status_code=404, content={"error": "not found"})
	asyncio.create_task(_simulate_progress(task_id))
	return {"ok": True}

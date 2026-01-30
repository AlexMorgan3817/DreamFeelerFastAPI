from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import os
import json
import shutil
from subprocess import Popen, PIPE, STDOUT

from hashlib import md5
import time
from datetime import datetime
# from pathlib import Path
import re

from typing import *

from ports import Ports

app = FastAPI()
app.mount("/static", StaticFiles(directory="html/"), name="static")
#Ports[PortNumber, IsUsed?]
PortsPool:Ports = Ports(50000, 50100)
templates = Jinja2Templates(directory="html/templates")
DEBUG = False
LOGSELF = False
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
	return templates.TemplateResponse("le_compiler.html", {"request": request})

@app.websocket("/ws/compile/")
async def websocket_compile(websocket: WebSocket):
	await websocket.accept()
	compile_in_progress = False
	try:
		while True:
			data = await websocket.receive_text()
			try:
				data_json = json.loads(data)
			except Exception:
				await websocket.send_text(json.dumps({"logdata": "Invalid JSON"}))
				continue
			if 'data_to_compile' in data_json:
				if compile_in_progress:
					continue
				compile_in_progress = True
				code = data_json['data_to_compile']
				await compile_code(websocket, code)
				compile_in_progress = False
				await websocket.send_text(json.dumps({"unlock": True}))
			# elif 'data_to_save' in data_json: # Moved to frontend
			# 	await websocket.send_text(json.dumps({"logdata": "Saved"}))
	except WebSocketDisconnect:
		print("User disconnected.")

async def send(ws:WebSocket, message:Union[str, dict]):
	if isinstance(message, dict):
		return await ws.send_text(json.dumps(message))
	return await ws.send_text(json.dumps({"logdata": message}))

async def compile_code(ws: WebSocket, code: str, dataDir:str="compile_data/"):
	if "#" in code:
		await send(ws, "SecError: #directives are prohibbiten for security reasons.")
		return
	if "sleep" in code:
		await send(ws, "Warning: Use of sleep are not recomended, your script have only 1 second to execute.\n")
	if "shell" in code:
		await send(ws, "Error: Security violation: Shell() in code.\n")
		return
	if "call" in code:
		await send(ws, "Error: Security violation: Call() in code.\n")
		return
	if re.search(r"([/ ]*)world([/ ]*)New()", code):
		await send(ws, "SecError: overriding of /world/New()(Use MAIN instead) are prohibbiten for security reasons.")
		return
	if 'world' in code:
		await send(ws, "SecError: using of /world/ is prohibitten.")
		return
	template:Optional[str] = None
	try:
		with open(dataDir + "template.dme", 'r') as t_file:
			template = t_file.read()
	except Exception as e:
		await ws.send_text(json.dumps({"logdata":"There is no DME preview, contact author."}))
		raise e
		return
	d = datetime.now()
	dateid = d.strftime('%Y%m%d%H%M%S')
	if DEBUG:
		compilation_id = d.strftime("%Y%m%d%H%M%S")
	else:
		compilation_id = f"{md5((dateid + str(ws)).encode('utf-8')).hexdigest()}"
	os.makedirs(dataDir + f"{compilation_id}/", exist_ok=True)
	projectDir = dataDir + f"{compilation_id}/"
	coreFilePath = f"{projectDir}{compilation_id}"
	dmeFilePath  = coreFilePath + ".dme"
	dmFilePath   = coreFilePath + ".dm"
	# Path(projectDir).mkdir(parents=True, exist_ok=True)
	with open(dmeFilePath, 'w') as dmeFile:
		dmeFile.write(template.replace("%FILENAME%", compilation_id))
	with open(dmFilePath, 'w') as dmf:
		dmf.write(code)
	command = dmeFilePath
	await send(ws, dmeFilePath)
	if os.environ.get('OS','') == 'Windows_NT':
		command = 'dm.exe ' + command
	else:
		command = 'dm ' + command
	p:Popen = Popen(command, stdout = PIPE, stderr = STDOUT, shell = False)
	if not p.stdout:
		await send(ws, "Error in output has occured.")
		return
	for line in p.stdout:
		await send(ws, line.decode("utf-8"))
	await send(ws, "\nRunning program.\n\n")
	# time.sleep(1)
	# p.terminate()
	try:
		port:Optional[int] = PortsPool.get_port()
		if not port:
			await send(ws, "There is no port available. Please wait.")
			return
		command = f'"{coreFilePath}.dmb" {port} -invisible -ultrasafe -logself'
		if os.environ.get('OS','') == 'Windows_NT':
			command = 'dreamdaemon.exe ' + command
		else:
			command = 'dreamdaemon ' + command
		print(f"Executing: {command}")
		p = Popen(command, stdout = PIPE, stderr = STDOUT, shell=False)
		# for line in p.stdout:
		# 	if line == "//STOP":
		# 		break
		# 	await websocket.send_text(json.dumps({"logdata": line.decode("utf-8")}))
		print(f"Awaiting to finish: {p}")
		print("Stop process")
		time.sleep(1)
		p.terminate()
		PortsPool.release_port(port)
		try:
			with open(coreFilePath + ".log", 'r') as logfile:
				await send(ws, logfile.read())
		except IOError as e:
			await send(ws, "Error in output has occured.")
			raise e
	except Exception as e:
		await send(ws, "Execution error.")
		raise e
	time.sleep(1)
	if not LOGSELF:
		shutil.rmtree(projectDir, ignore_errors=True)
	await send(ws, {'unlock': True})

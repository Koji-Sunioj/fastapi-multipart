import re
import os
import math
import json 
import shutil
import base64
import chardet
from pathlib import Path
from typing import List
from typing_extensions import Annotated
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import FastAPI, File, UploadFile, Request

app = FastAPI()

class Server:
    files_path = os.getcwd()+"/files/"

    def create_files_folder(self):
        cwd = os.listdir(os.getcwd())
        if "files" not in cwd:
            os.makedirs(self.files_path)

server = Server()
server.create_files_folder()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    mbs = int(request.headers["content-length"]) /1024/1000
    if mbs > 10:
        return JSONResponse({"detail":"payload too large"},415)
    response = await call_next(request)
    return response

@app.post("/files/")
async def create_files(request: Request):
    response = None
    try:
        content = await request.form()
        written_files = []
        for file in content.keys():
            raw_file = content[file].file   
            raw_file.seek(0)
            file_content = raw_file.read()
            file_path = server.files_path+content[file].filename
            new_file = open(file_path,"wb")
            new_file.write(file_content)
            new_file.close()
            written_files.append(content[file].filename)
        
        is_written = all([existing in written_files for existing in os.listdir(server.files_path)])
        
        if is_written: 
            message =  ", ".join(written_files) + " written to the server"
            response = JSONResponse({"detail":message},200)
        else:
            response = JSONResponse({"detail":"error happened"},400)       
    except Exception as error:
        response = JSONResponse({"detail":str(error)},500)     
    return response
    

def retrieve_string(pattern,string):
    found_bytes = re.search(pattern, string)
    start, stop = found_bytes.start(), found_bytes.end()
    return string[start:stop]


@app.post("/multipart/")
async def create_files(request: Request):
    response = None
    try:
        content_type = request.headers["content-type"]
        pattern = r"(?<=boundary=).*"
        boundary = retrieve_string(pattern, content_type)

        body = await request.body()
        chunk_pattern = bytes("(?s)(?<=--%s).*?(?=--%s)" % (boundary,boundary),"utf-8")
        chunks = re.findall(chunk_pattern, body)

        written_files = []
        filename_pattern = b"(?<=filename=)(.*)"     

        for chunk in chunks:
            filename = retrieve_string(filename_pattern, chunk).decode("utf-8").replace('"','')
            print(filename)
            file_line = 4
            groups = chunk.split(b"\n")
            byte_line = b"\n".join(groups[:file_line]), b"\n".join(groups[file_line:])
            file_path = server.files_path+filename
            new_file = open(file_path,"wb")
            new_file.write(byte_line[1])
            new_file.close()
            written_files.append(filename.rstrip())
        
        message =  ", ".join(written_files) + " written to the server"
        response = JSONResponse({"detail":message},200)        
    except Exception as error:
        response = JSONResponse({"detail":str(error)},500)     
    return response
    
  

# _*_ coding:utf-8 _*_
# @File  : main.py
# @Time  : 2020-08-31 8:21
# @Author: zizle

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from routers import router
from configs import FILE_STORAGE

app = FastAPI()

app.mount("/static/", StaticFiles(directory=FILE_STORAGE), name="staticFiles")


@app.get("/", tags=["主页"])
async def index():
    home_page = os.path.join(FILE_STORAGE, "home_page.html")
    return FileResponse(home_page)


@app.get("/favicon.ico", tags=["主页"])
async def favicon():
    favicon_path = os.path.join(FILE_STORAGE, "favicon.ico")
    return FileResponse(favicon_path, filename="favicon.ico")


@app.get("/download/client/{sys_platform}/{sys_bit}/", tags=["下载"], summary="安装文件下载")
async def download_client(sys_platform: str, sys_bit: str):
    if sys_bit not in ["x32", "x64"]:
        raise HTTPException(status_code=404, detail="THE INSTALLER NOT FOUND!")
    if sys_platform not in ["WIN7", "WIN10"]:
        raise HTTPException(status_code=404, detail="THE INSTALLER NOT FOUND!")
    filename = "FAClientSetup_{}_{}.exe".format(sys_platform, sys_bit)
    client_file = os.path.join(FILE_STORAGE, "INSTALLER/{}/OUTSIDE/{}/{}".format(sys_platform, sys_bit, filename))
    if not os.path.exists(client_file):
        raise HTTPException(status_code=404, detail="THE INSTALLER NOT FOUND!")
    return FileResponse(client_file, filename=filename)


app.include_router(router, prefix='/api')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
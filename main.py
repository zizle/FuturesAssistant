# _*_ coding:utf-8 _*_
# @File  : main.py
# @Time  : 2020-08-31 8:21
# @Author: zizle

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
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


app.include_router(router, prefix='/api')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
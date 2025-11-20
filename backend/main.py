from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# 这是一个简单的 HTTP 接口，测试网站活没活着
@app.get("/")
async def get():
    return {"message": "Texas Poker Server is running!"}

# 这是一个 WebSocket 接口，用于实时通信
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("正在等待连接...")
    await websocket.accept() # 接受前端的连接
    print("前端已连接！")
    
    try:
        while True:
            # 1. 等待前端发送消息
            data = await websocket.receive_text()
            print(f"收到前端消息: {data}")
            
            # 2. 发送回复给前端
            response = f"服务器收到了你的消息: {data}"
            await websocket.send_text(response)
    except Exception as e:
        print("连接断开")
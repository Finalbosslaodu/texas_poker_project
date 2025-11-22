import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.core.game_engine import GameEngine
from backend.core.player import Player
from backend.core.ai import PokerAI # 改名了
from backend.api.manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
game = GameEngine()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # 辅助：AI 自动准备 (仅在游戏循环中有效)
    async def make_ai_ready():
        if game.stage == "SHOWDOWN":
            await asyncio.sleep(1) 
            for p in game.players:
                # [修复] 移除 p.chips > 0 的判断。
                # 只要是 AI，到了结算界面就自动准备。
                # 即使 AI 输光了，标记为 Ready 也不影响下一局的 start_game 逻辑（它会自动过滤掉筹码为0的人）。
                if p.is_ai and not p.is_ready:
                    game.set_player_ready(p.name)
            await manager.broadcast(game.get_state())

    # 辅助：AI 思考循环
    async def process_ai_turns():
        while True:
            if game.stage == "LOBBY": break # 大厅不思考
            if game.stage == "SHOWDOWN":
                await make_ai_ready()
                break 

            current = game.players[game.current_player_idx]
            if not current.is_ai or current.status != "active": break
            
            print(f"[AI Lv{current.ai_level}] {current.name} thinking...")
            await asyncio.sleep(0.5 + (current.ai_level * 0.1)) # 高等级想慢点? 或者快点
            
            ai_action, ai_amt = PokerAI.decide(current, game.get_state())
            game.handle_action(current.name, ai_action, ai_amt)
            await manager.broadcast(game.get_state())

    # 连接后发送当前状态
    await manager.broadcast(game.get_state())

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            # --- LOBBY 指令 ---
            if action == "sit":
                seat_idx = data.get("seat")
                name = data.get("name", "Player")
                # [修改] 读取前端传来的 chips，如果没有则默认 10000
                chips = data.get("chips", 10000)
                p = Player(name, chips, is_ai=False)
                success, msg = game.sit_player(p, seat_idx)
                await manager.broadcast(game.get_state())

            elif action == "add_bot":
                seat_idx = data.get("seat")
                level = data.get("level", 0)
                game.add_bot(seat_idx, level)
                await manager.broadcast(game.get_state())

            elif action == "start_game":
                success, msg = game.start_game_from_lobby()
                await manager.broadcast(game.get_state())
                if success: await process_ai_turns()

            # --- 游戏指令 ---
            elif action == "ready":
                game.set_player_ready("You") # 这里假设目前只有一个人类叫You
                await manager.broadcast(game.get_state())
                if game.stage == "PREFLOP": await process_ai_turns()

            else: # Fold, Call, Raise
                # 简单的鉴权：假设前端发来的 action 就是 "You" 的
                # 实际多人联机这里要用 websocket 对应的 session id 来判断
                current = game.players[game.current_player_idx]
                if current.name == "You" or current.name == data.get("playerName"): 
                    amount = data.get("amount", 0)
                    success, msg = game.handle_action(current.name, action, amount)
                    if success:
                        await manager.broadcast(game.get_state())
                        await process_ai_turns()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
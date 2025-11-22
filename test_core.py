from backend.core.game_engine import GameEngine
from backend.core.player import Player

# 初始化游戏
game = GameEngine()
p1 = Player("Alice", 1000)
p2 = Player("Bob", 1000)
game.add_player(p1)
game.add_player(p2)

# 开始
print("--- 1. 开始游戏 ---")
game.start_game()
print(f"盲注阶段: Pot={game.pot}, P1 bet={p1.round_bet}, P2 bet={p2.round_bet}")
print(f"当前行动: {game.players[game.current_player_idx].name}")

# Alice (SB) 跟注 10 (变成20)
print("\n--- 2. Alice 跟注 ---")
success, msg = game.handle_action("Alice", "call")
print(f"Alice 操作结果: {success} - {msg}")

# Bob (BB) Check
print("\n--- 3. Bob Check ---")
success, msg = game.handle_action("Bob", "check") # 此时 Bob 已经下过20了，to_call=0
print(f"Bob 操作结果: {success} - {msg}")

# 应该进入 FLOP
print("\n--- 4. 进入 FLOP ---")
state = game.get_state()
print(f"当前阶段: {state['stage']}")
print(f"公共牌: {state['community_cards']}")
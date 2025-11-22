from .card import Deck
from .evaluator import HandEvaluator
from .player import Player

class GameEngine:
    def __init__(self):
        self.max_seats = 12
        self.seats = [None] * self.max_seats
        self.players = []
        
        self.deck = None
        self.community_cards = []
        self.pot = 0 # 这里的 pot 仅作为显示用，实际结算是基于 total_bet 计算的
        self.current_bet = 0
        self.dealer_absolute_idx = 0
        self.current_player_idx = 0
        
        self.stage = "LOBBY"
        self.min_raise = 20
        self.acted_players = set()
        self.big_blind = 20

    # --- 座位管理 (保持不变) ---
    def sit_player(self, player, seat_idx):
        if not (0 <= seat_idx < self.max_seats): return False, "座位不存在"
        if self.seats[seat_idx] is not None: return False, "座位已满"
        player.seat_id = seat_idx
        self.seats[seat_idx] = player
        return True, "入座成功"

    def add_bot(self, seat_idx, difficulty):
        # [修改] 名字简化为 Bot (S{seat_idx})，因为风格会单独显示
        bot_name = f"Bot (S{seat_idx})"
        
        # 创建时 Player 内部会自动随机风格
        bot = Player(bot_name, 10000, is_ai=True, ai_level=difficulty)
        return self.sit_player(bot, seat_idx)

    def remove_player(self, seat_idx):
        if 0 <= seat_idx < self.max_seats: self.seats[seat_idx] = None

    def start_game_from_lobby(self):
        return self.start_game()

    # --- 核心流程 ---

    def start_game(self):
        # 1. 筛选有筹码的玩家
        round_players = [p for p in self.seats if p is not None and p.chips > 0]
        if len(round_players) < 2: 
            self.stage = "LOBBY"
            return False, "筹码不足"

        self.players = round_players
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.stage = "PREFLOP"
        self.acted_players.clear()
        
        for p in self.players:
            p.reset_for_round()
            p.hand = [self.deck.deal(), self.deck.deal()]

        # Dealer 轮转
        self.players.sort(key=lambda x: x.seat_id)
        dealer_idx = 0
        for i, p in enumerate(self.players):
            if p.seat_id >= self.dealer_absolute_idx:
                dealer_idx = i
                break
        dealer_idx = (dealer_idx + 1) % len(self.players)
        self.dealer_absolute_idx = self.players[dealer_idx].seat_id
        
        # 盲注
        sb_idx = (dealer_idx + 1) % len(self.players)
        bb_idx = (dealer_idx + 2) % len(self.players)
        if len(self.players) == 2:
            sb_idx = dealer_idx
            bb_idx = (dealer_idx + 1) % len(self.players)

        sb_player = self.players[sb_idx]
        bb_player = self.players[bb_idx]

        self._player_bet(sb_player, min(sb_player.chips, self.big_blind // 2))
        self._player_bet(bb_player, min(bb_player.chips, self.big_blind))
        
        self.current_bet = self.big_blind
        self.current_player_idx = (bb_idx + 1) % len(self.players)
        
        self._ensure_active_player()
        return True, "新一局开始"

    def set_player_ready(self, player_name):
        if self.stage == "LOBBY": return False, "请点击开始游戏"
        for p in self.seats:
            if p and p.name == player_name: p.is_ready = True
        
        capable_players = [p for p in self.seats if p is not None and p.chips > 0]
        if not capable_players: return False, "无人可用"
        
        if all(p.is_ready for p in capable_players):
            return self.start_game()
        return True, "已准备"

    def handle_action(self, player_name, action_type, amount=0):
        player = self.players[self.current_player_idx]
        if player.name != player_name: return False, "不是你的回合"
        to_call = self.current_bet - player.round_bet

        if action_type == 'fold':
            player.status = 'folded'
        elif action_type == 'call':
            actual_bet = min(to_call, player.chips)
            self._player_bet(player, actual_bet)
        elif action_type == 'check':
            if to_call > 0: return False, "必须跟注或弃牌"
        elif action_type == 'raise':
            if amount < self.current_bet: return False, "金额错误"
            diff = amount - player.round_bet
            if diff > player.chips: return False, "筹码不足"
            self._player_bet(player, diff)
            if amount > self.current_bet:
                self.current_bet = amount
                self.acted_players.clear()

        self.acted_players.add(player.name)
        self._next_turn()
        return True, "操作成功"

    def _player_bet(self, player, amount):
        if amount <= 0: return
        if amount > player.chips: amount = player.chips
        player.chips -= amount
        player.round_bet += amount
        player.total_bet += amount # 关键：累积总投入，用于算边池
        self.pot += amount
        if player.chips == 0: player.status = 'allin'

    def _ensure_active_player(self):
        if all(p.status != 'active' for p in self.players): return
        start_idx = self.current_player_idx
        while self.players[self.current_player_idx].status != 'active':
             self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
             if self.current_player_idx == start_idx: break

    def _next_turn(self):
        start_idx = self.current_player_idx
        not_folded = [p for p in self.players if p.status != 'folded']
        if len(not_folded) == 1:
            self._resolve_winner()
            return

        active_players = [p for p in self.players if p.status == 'active']
        should_fast_forward = False
        if len(active_players) == 0: should_fast_forward = True
        elif len(active_players) == 1:
            p = active_players[0]
            if p.round_bet >= self.current_bet: should_fast_forward = True
        
        if should_fast_forward:
            while self.stage != "SHOWDOWN": self._next_stage(auto_roll=True)
            return

        for i in range(1, len(self.players) + 1):
            idx = (start_idx + i) % len(self.players)
            p = self.players[idx]
            if p.status == 'active':
                if p.round_bet < self.current_bet or p.name not in self.acted_players:
                    self.current_player_idx = idx
                    return
        self._next_stage()

    def _next_stage(self, auto_roll=False):
        for p in self.players: p.round_bet = 0
        self.current_bet = 0
        self.acted_players.clear()
        
        if self.stage == "PREFLOP":
            self.stage = "FLOP"
            self.community_cards = [self.deck.deal() for _ in range(3)]
        elif self.stage == "FLOP":
            self.stage = "TURN"
            self.community_cards.append(self.deck.deal())
        elif self.stage == "TURN":
            self.stage = "RIVER"
            self.community_cards.append(self.deck.deal())
        elif self.stage == "RIVER":
            self.stage = "SHOWDOWN"
            self._resolve_winner()
            return

        if auto_roll: return

        dealer_list_idx = 0
        for i, p in enumerate(self.players):
            if p.seat_id == self.dealer_absolute_idx:
                dealer_list_idx = i; break
        self.current_player_idx = (dealer_list_idx + 1) % len(self.players)
        self._ensure_active_player()

    def _resolve_winner(self):
        # [重点] 边池算法实现
        
        # 1. 收集所有未弃牌玩家，按总投入(total_bet)排序
        # 弃牌者的钱已经死在池子里了，谁赢主池谁拿走
        candidates = [p for p in self.players if p.status != 'folded']
        candidates.sort(key=lambda p: p.total_bet)
        
        # 计算每个人的贡献池
        pots = [] # 结构: [{'amount': 1000, 'contributors': [p1, p2...]}, ...]
        
        # 这里的算法：
        # 我们一层层“削平”每个人的投入。
        # 比如 A投10(allin), B投50, C投50.
        # 第一层(Side Pot 0/Main): 每人取10。池子=30。参与者=ABC。如果A赢了，拿走30。
        # 剩下: A=0, B=40, C=40。
        # 第二层(Side Pot 1): 每人取40。池子=80。参与者=BC。如果B赢了，拿走80。A没资格。
        
        # 为了处理方便，我们还需要把 Folded 玩家的钱也算进去（死钱）
        # 简单的做法：把所有人的 total_bet 拿出来处理
        
        all_bets = [p.total_bet for p in self.players if p.total_bet > 0]
        all_bets = sorted(list(set(all_bets))) # 去重并排序层级，例如 [10, 50]
        
        last_bet_level = 0
        
        for bet_level in all_bets:
            pot_amount = 0
            contributors = []
            
            diff = bet_level - last_bet_level
            
            for p in self.players:
                if p.total_bet >= bet_level:
                    pot_amount += diff
                    if p.status != 'folded':
                        contributors.append(p)
                elif p.total_bet > last_bet_level:
                    # 比如某人allin了 5块，但这层是 10块
                    # 他的贡献是 (5 - 0) = 5
                    pot_amount += (p.total_bet - last_bet_level)
                    # 他没有资格赢这层（因为他这层没钱了）
            
            if pot_amount > 0:
                pots.append({
                    "amount": pot_amount,
                    "contributors": contributors
                })
            
            last_bet_level = bet_level

        # 结算每个池子
        for pot in pots:
            if not pot['contributors']: continue # 理论上不可能，除非全是死钱
            
            # 找出这个池子的赢家
            best_score = (-1, [])
            winners = []
            
            for p in pot['contributors']:
                score = HandEvaluator.evaluate(p.hand, self.community_cards)
                if score > best_score:
                    best_score = score
                    winners = [p]
                elif score == best_score:
                    winners.append(p)
            
            if winners:
                share = pot['amount'] // len(winners)
                extra = pot['amount'] % len(winners)
                for w in winners:
                    w.chips += share
                winners[0].chips += extra

        # 计算本局盈亏
        for p in self.players:
            p.round_profit = p.chips - p.start_chips
        
        # [新增] 自动重买逻辑
        for p in self.seats:
            if p is not None and p.chips == 0:
                p.chips = 10000
                p.rebuy_count += 1
                # 重置其盈亏显示为本局输掉的数额（通常是 -start_chips）
                # 但因为我们刚刚把chips改了，round_profit 如果依赖 p.chips - start 就会变成正数
                # 为了显示自然，我们保持 round_profit 不变 (即显示 -10000)，下一局开始时 start_chips 会更新为 10000
        
        self.stage = "SHOWDOWN"

    def get_state(self):
        if self.stage == "LOBBY":
            return {
                "stage": "LOBBY",
                "seats": [p.to_dict() if p else None for p in self.seats],
                "max_seats": self.max_seats
            }
        return {
            "stage": self.stage,
            "pot": self.pot,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "current_bet": self.current_bet,
            "current_player": self.players[self.current_player_idx].name if self.stage != "SHOWDOWN" and self.players else None,
            "players": [p.to_dict(include_hand=True) for p in self.players],
            "seats": [p.to_dict(include_hand=True) if p else None for p in self.seats] 
        }
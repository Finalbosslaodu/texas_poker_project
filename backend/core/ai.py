import random
from .evaluator import HandEvaluator
from .card import Deck, Card

class AIStyle:
    """
    AI 风格定义
    包含对决策阈值的修正参数
    """
    def __init__(self, name, label, vpip_mod=0, agg_mod=0, bluff_prob=0):
        self.name = name      # 内部代号
        self.label = label    # 显示名称
        self.vpip_mod = vpip_mod # 入局率修正 (Loose/Tight) -> 影响 Call 门槛
        self.agg_mod = agg_mod   # 激进率修正 (Passive/Aggressive) -> 影响 Raise 门槛
        self.bluff_prob = bluff_prob # 诈唬概率

# 定义 6 种风格配置
STYLES = {
    "rock": AIStyle("rock", "🪨 Rock", vpip_mod=-0.15, agg_mod=-0.1, bluff_prob=0.02),
    "fish": AIStyle("fish", "🐟 Fish", vpip_mod=0.2, agg_mod=-0.5, bluff_prob=0.05),
    "maniac": AIStyle("maniac", "💣 Maniac", vpip_mod=0.15, agg_mod=0.3, bluff_prob=0.4),
    "shark": AIStyle("shark", "🦈 Shark", vpip_mod=0, agg_mod=0.15, bluff_prob=0.15),
    "gambler": AIStyle("gambler", "🎭 Gambler", vpip_mod=0.25, agg_mod=0.1, bluff_prob=0.2),
    "gto": AIStyle("gto", "🤖 GTO", vpip_mod=0, agg_mod=0, bluff_prob=0.1),
}

class PokerAI:
    """
    8 个智力等级：
    Lv0-1: 随机/极简
    Lv2-4: 基础数学 (Pot Odds)
    Lv5-7: 蒙特卡洛模拟 (Win Rate) + 风格修正
    """

    @staticmethod
    def decide(player, game_state):
        level = player.ai_level
        style_key = getattr(player, 'ai_style', 'fish') # 默认 Fish
        style = STYLES.get(style_key, STYLES['fish'])
        
        # 补全数据
        if 'min_raise' not in game_state: game_state['min_raise'] = 20

        # --- 低智力阶段 (Lv0 - Lv2) ---
        # 纯随机或仅看手牌大小，不考虑公共牌配合
        if level == 0: 
            return PokerAI._action_random(player, game_state)
        
        if level == 1:
            # 简单的手牌强弱判断 (高牌/对子)
            return PokerAI._action_simple(player, game_state, style, threshold=0.6)

        if level == 2:
             # 稍微紧一点的新手
            return PokerAI._action_simple(player, game_state, style, threshold=0.4)

        # --- 中智力阶段 (Lv3 - Lv4) ---
        # 开始计算底池赔率，但胜率估算很粗糙 (低次数模拟)
        if level == 3:
            return PokerAI._action_simulated(player, game_state, style, simulations=20)
        
        if level == 4:
            return PokerAI._action_simulated(player, game_state, style, simulations=50)

        # --- 高智力阶段 (Lv5 - Lv7) ---
        # 高精度模拟 + 风格深度影响 + 诈唬
        if level == 5:
            return PokerAI._action_simulated(player, game_state, style, simulations=100)
        
        if level == 6:
            return PokerAI._action_simulated(player, game_state, style, simulations=200)
            
        if level == 7:
            # 顶尖 AI：模拟次数高，且根据对手位置调整 (模拟中简单体现)
            return PokerAI._action_simulated(player, game_state, style, simulations=300)

        return 'call', 0

    # -------------------------------------------------------------------------
    # 核心算法实现
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_win_rate(hand, community_cards_data, simulations=100):
        """
        蒙特卡洛模拟计算胜率 (Equity)
        """
        community_cards = []
        for c_data in community_cards_data:
            if isinstance(c_data, dict):
                community_cards.append(Card(c_data['rank'], c_data['suit']))
            else:
                community_cards.append(c_data)

        wins = 0
        known_cards = hand + community_cards
        known_keys = { (c.rank, c.suit) for c in known_cards }

        for _ in range(simulations):
            deck = Deck()
            deck.cards = [c for c in deck.cards if (c.rank, c.suit) not in known_keys]
            deck.shuffle()
            
            needed = 5 - len(community_cards)
            if len(deck.cards) >= needed + 2:
                sim_comm = community_cards + [deck.deal() for _ in range(needed)]
                opp_hand = [deck.deal(), deck.deal()]
                
                my_score = HandEvaluator.evaluate(hand, sim_comm)
                opp_score = HandEvaluator.evaluate(opp_hand, sim_comm)
                
                if my_score > opp_score: wins += 1
                elif my_score == opp_score: wins += 0.5
        
        return wins / simulations if simulations > 0 else 0

    @staticmethod
    def _action_random(p, g):
        """Lv0: 瞎玩"""
        action = random.choice(['call', 'fold', 'raise', 'check'])
        if action == 'raise':
            target = g['current_bet'] * 2 + random.randint(0, 100)
            return PokerAI._make_valid_raise(p, g, target)
        return action, 0

    @staticmethod
    def _action_simple(p, g, style, threshold):
        """Lv1-2: 基于手牌强度的简单逻辑"""
        # 没发公共牌前，只看起手牌
        if not g['community_cards']:
            val = p.hand[0].rank + p.hand[1].rank
            is_pair = p.hand[0].rank == p.hand[1].rank
            # 岩石需要更大牌，疯子小牌也玩
            score = (val / 28.0) + (0.2 if is_pair else 0) + style.vpip_mod
            
            if score > threshold:
                if score > threshold + 0.3 + style.agg_mod:
                    return PokerAI._make_valid_raise(p, g, g['big_blind']*3)
                return 'call', 0
            
            # 如果可以 check，就 check，否则根据风格 fold
            to_call = g['current_bet'] - p.round_bet
            return ('check', 0) if to_call == 0 else ('fold', 0)
        
        # 发了公共牌，简单评估是否有对子
        score_rank, _ = HandEvaluator.evaluate(p.hand, []) # 这里有个小bug，应该传community，下行修复
        # 重新转换 community
        comm = []
        for c in g['community_cards']:
            comm.append(Card(c['rank'], c['suit']) if isinstance(c, dict) else c)
            
        score_rank, _ = HandEvaluator.evaluate(p.hand, comm)
        
        # 1=HighCard, 2=Pair ...
        # 如果有对子(2)以上，大概率跟
        if score_rank >= 2:
            return 'call', 0
        
        to_call = g['current_bet'] - p.round_bet
        return ('check', 0) if to_call == 0 else ('fold', 0)

    @staticmethod
    def _action_simulated(p, g, style, simulations):
        """Lv3-7: 基于胜率模拟 + 风格修正"""
        win_rate = PokerAI._get_win_rate(p.hand, g['community_cards'], simulations)
        
        # 1. 修正胜率 (Perceived Equity)
        # 松凶玩家会高估自己的胜率，紧弱玩家会低估
        perceived_equity = win_rate * (1.0 + style.agg_mod) 
        
        # 2. 计算底池赔率 (Pot Odds)
        to_call = g['current_bet'] - p.round_bet
        pot_total = g['pot'] + to_call
        pot_odds = to_call / pot_total if pot_total > 0 else 0
        
        # 3. 决策逻辑
        
        # 3.1 诈唬判定 (Bluff)
        # 只有当不需要投入太多(或者决定Allin)，且胜率很低时尝试
        if win_rate < 0.3 and random.random() < style.bluff_prob:
            # 诈唬加注
            target = g['pot'] * (0.5 + random.random()) # 0.5~1.5倍底池
            return PokerAI._make_valid_raise(p, g, target)

        # 3.2 强牌加注 (Value Bet)
        # 胜率显著高于底池赔率，且风格激进
        if perceived_equity > pot_odds + 0.3:
            # 随机决定是慢打(Slow Play)还是加注
            if random.random() > 0.2: 
                target = g['pot'] * (0.6 + style.agg_mod) # 根据激进程度决定注码
                return PokerAI._make_valid_raise(p, g, target)

        # 3.3 跟注/过牌 (Call/Check)
        if perceived_equity >= pot_odds - style.vpip_mod: # vpip_mod 越高越容易跟注
            if to_call == 0: return 'check', 0
            return 'call', 0
            
        # 3.4 弃牌 (Fold)
        if to_call == 0: return 'check', 0
        return 'fold', 0

    @staticmethod
    def _make_valid_raise(p, g, target_amount):
        """合法加注辅助函数"""
        current_bet = g['current_bet']
        min_raise = g.get('min_raise', 20)
        min_total = current_bet + min_raise
        
        # 1. 如果目标加注额太小，甚至不够跟注
        if target_amount <= current_bet:
            return 'call', 0
            
        # 2. 修正到最小合法加注
        if target_amount < min_total:
            target_amount = min_total
            
        # 3. 检查资金
        needed = target_amount - p.round_bet
        if needed >= p.chips:
            return 'call', 0 # All-in by call logic
            
        return 'raise', int(target_amount)
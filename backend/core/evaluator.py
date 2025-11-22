from collections import Counter

class HandEvaluator:
    @staticmethod
    def evaluate(hole_cards, community_cards):
        """
        返回: (分数等级, [关键牌列表])
        分数等级: 9=同花顺, 8=四条, ..., 1=高牌
        """
        cards = hole_cards + community_cards
        if not cards: return (0, [])
        
        # 排序
        cards.sort(key=lambda c: c.rank, reverse=True)
        ranks = [c.rank for c in cards]
        suits = [c.suit for c in cards]
        
        # 辅助数据
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # 1. 检查同花
        flush_suit = next((s for s, c in suit_counts.items() if c >= 5), None)
        flush_cards = [c for c in cards if c.suit == flush_suit] if flush_suit else []
        
        # 2. 检查顺子 (辅助函数)
        def get_straight_high(unique_ranks):
            for i in range(len(unique_ranks)-4):
                if unique_ranks[i] - unique_ranks[i+4] == 4:
                    return unique_ranks[i]
            # 特殊 A-5 顺子 (A, 5, 4, 3, 2)
            if {14, 5, 4, 3, 2}.issubset(set(unique_ranks)):
                return 5
            return -1

        unique_ranks = sorted(list(set(ranks)), reverse=True)
        straight_high = get_straight_high(unique_ranks)

        # --- 判定逻辑 ---
        
        # 同花顺
        if flush_cards:
            f_ranks = sorted(list(set(c.rank for c in flush_cards)), reverse=True)
            f_straight = get_straight_high(f_ranks)
            if f_straight != -1:
                return (9, [f_straight])
        
        # 四条
        quads = [r for r, n in rank_counts.items() if n == 4]
        if quads:
            kicker = [r for r in ranks if r != quads[0]][0]
            return (8, [quads[0], kicker])
            
        # 葫芦
        trips = [r for r, n in rank_counts.items() if n == 3]
        pairs = [r for r, n in rank_counts.items() if n == 2]
        if trips:
            t = trips[0] # 最大三条
            # 找对子或第二个三条作为附带的对子
            remaining = [r for r in ranks if r != t]
            rem_counts = Counter(remaining)
            p = next((r for r, n in rem_counts.items() if n >= 2), None)
            if p:
                return (7, [t, p])
        
        # 同花
        if flush_cards:
            return (6, [c.rank for c in flush_cards[:5]])
            
        # 顺子
        if straight_high != -1:
            return (5, [straight_high])
            
        # 三条
        if trips:
            kickers = [r for r in ranks if r != trips[0]][:2]
            return (4, [trips[0]] + kickers)
            
        # 两对
        if len(pairs) >= 2:
            pairs.sort(reverse=True)
            kicker = [r for r in ranks if r not in pairs[:2]][0]
            return (3, pairs[:2] + [kicker])
            
        # 一对
        if pairs:
            kickers = [r for r in ranks if r != pairs[0]][:3]
            return (2, [pairs[0]] + kickers)
            
        # 高牌
        return (1, ranks[:5])
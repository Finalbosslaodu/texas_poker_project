import random # 记得引入

class Player:
    def __init__(self, name, chips=10000, is_ai=False, ai_level=0, seat_id=-1):
        self.name = name
        self.chips = int(chips)
        self.hand = []
        self.is_ai = is_ai
        self.ai_level = ai_level
        self.seat_id = seat_id
        
        # [新增] 随机分配风格
        self.ai_style = 'fish' # 默认
        if is_ai:
            # 从所有风格中随机选一个
            styles = ["rock", "fish", "maniac", "shark", "gambler", "gto"]
            self.ai_style = random.choice(styles)

        self.status = "waiting" 
        self.round_bet = 0
        self.total_bet = 0
        self.is_ready = False
        self.start_chips = self.chips 
        self.round_profit = 0
        self.rebuy_count = 0

    def reset_for_round(self):
        self.hand = []
        self.round_bet = 0
        self.total_bet = 0
        self.is_ready = False
        self.start_chips = self.chips
        self.round_profit = 0
        
        if self.chips > 0:
            self.status = "active"
        else:
            self.status = "out"

    def to_dict(self, include_hand=False):
        # 这里需要把 ai_style 对应的 emoji 标签传给前端
        # 为了解耦，我们简单地把 style key 传过去，前端自己映射，或者后端映射好
        # 这里选择传 key 和 label
        from .ai import STYLES # 延迟导入避免循环引用
        style_data = STYLES.get(self.ai_style)
        style_label = style_data.label if style_data else self.ai_style

        data = {
            "name": self.name,
            "chips": self.chips,
            "round_bet": self.round_bet,
            "status": self.status,
            "is_ai": self.is_ai,
            "ai_level": self.ai_level,
            "ai_style": self.ai_style,  # [新增]
            "ai_style_label": style_label, # [新增] 用于显示
            "seat_id": self.seat_id,
            "is_ready": self.is_ready,
            "round_profit": self.round_profit,
            "rebuy_count": self.rebuy_count
        }
        if include_hand:
            data["hand"] = [c.to_dict() for c in self.hand]
        else:
            data["hand_count"] = len(self.hand)
        return data
import random

SUITS = ['♠', '♥', '♣', '♦']
# [修改] 10映射为'10'而不是'T'，方便前端直接显示
RANKS = {
    2:'2', 3:'3', 4:'4', 5:'5', 6:'6', 7:'7', 8:'8', 9:'9', 
    10:'10', 11:'J', 12:'Q', 13:'K', 14:'A'
}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{RANKS[self.rank]}{self.suit}"
    
    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "rank": self.rank,          # 数字用于比大小 (13)
            "rank_str": RANKS[self.rank], # [新增] 字符用于显示 (K)
            "suit": self.suit,
            "str": str(self)
        }

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for r in RANKS for s in SUITS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop() if self.cards else None
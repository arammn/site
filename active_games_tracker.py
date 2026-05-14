"""In-memory tracker for active game chats (optimization)."""

class ActiveGameTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'auctions'):
            self.auctions = set()
            self.lucky_draws = set()
            self.dice_games = set()

    def add_auction(self, chat_id: int):
        self.auctions.add(chat_id)

    def add_lucky_draw(self, chat_id: int):
        self.lucky_draws.add(chat_id)

    def add_dice_game(self, chat_id: int):
        self.dice_games.add(chat_id)

    def remove_auction(self, chat_id: int):
        self.auctions.discard(chat_id)

    def remove_lucky_draw(self, chat_id: int):
        self.lucky_draws.discard(chat_id)

    def remove_dice_game(self, chat_id: int):
        self.dice_games.discard(chat_id)

    def is_chat_active(self, chat_id: int) -> bool:
        return chat_id in self.auctions or chat_id in self.lucky_draws or chat_id in self.dice_games

    def clear(self):
        self.auctions.clear()
        self.lucky_draws.clear()
        self.dice_games.clear()
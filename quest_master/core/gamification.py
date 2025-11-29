from typing import Dict

class Gamification:
    def __init__(self):
        self.xp = 0
        self.achievements = []
        self.levels: Dict[str, int] = {
            "Ученик": 0,
            "Мастер пергаментов": 50,
            "Архимаг документов": 100
        }

    def award_xp(self, amount: int, reason: str):
        self.xp += amount
        self.achievements.append(f"+{amount} XP за {reason}")

    def get_current_level(self) -> str:
        for level, threshold in reversed(list(self.levels.items())):
            if self.xp >= threshold:
                return level
        return "Ученик"

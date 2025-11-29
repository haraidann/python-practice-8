from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QListWidget, QLabel
from quest_master.core.gamification import Gamification

class GamificationPanel(QWidget):
    def __init__(self, gamification: Gamification, parent=None):
        super().__init__(parent)
        self.gamification = gamification
        self.setWindowTitle("Панель достижений")
        layout = QVBoxLayout()

        self.level_label = QLabel(f"Уровень: {self.gamification.get_current_level()}")
        layout.addWidget(self.level_label)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)

        self.ach_list = QListWidget()
        layout.addWidget(self.ach_list)

        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        self.level_label.setText(f"Уровень: {self.gamification.get_current_level()} (XP: {self.gamification.xp})")
        next_threshold = next((t for l, t in self.gamification.levels.items() if t > self.gamification.xp), 100)
        self.progress.setValue(int((self.gamification.xp / next_threshold) * 100))
        self.ach_list.clear()
        self.ach_list.addItems(self.gamification.achievements)

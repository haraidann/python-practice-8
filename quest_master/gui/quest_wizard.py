from __future__ import annotations
import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QRegularExpression, QDateTime, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator, QKeySequence, QShortcut

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox
)

from quest_master.core.database import Database
from quest_master.core.gamification import Gamification

def count_words(text: str) -> int:
    return len([w for w in text.strip().split() if w])

class QuestWizard(QWidget):
    closed = pyqtSignal()
    
    def __init__(self, db: Database, gamification: Optional[Gamification] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quest Wizard — Редактор квеста")
        self.db = db
        self.gamification = gamification
        self.current_quest_id: Optional[int] = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        form = QFormLayout()

        self.title_edit = QLineEdit()
        regex = QRegularExpression(r"^.{0,50}$")
        self.title_edit.setValidator(QRegularExpressionValidator(regex, self))
        self.title_hint = QLabel("Максимум 50 символов.")
        form.addRow("Название:", self.title_edit)
        form.addRow("", self.title_hint)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Легкий", "Средний", "Сложный", "Эпический"])
        form.addRow("Сложность:", self.difficulty_combo)

        self.reward_spin = QSpinBox()
        self.reward_spin.setRange(10, 10000)
        self.reward_spin.setSingleStep(10)
        self.reward_spin.setValue(100)
        form.addRow("Награда (XP):", self.reward_spin)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Опишите квест — минимум 50 слов.")
        self.desc_counter = QLabel("Слов: 0 | Символов: 0")
        form.addRow("Описание:", self.description_edit)
        form.addRow("", self.desc_counter)

        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDateTime(QDateTime.currentDateTime().addDays(7))
        form.addRow("Дедлайн:", self.deadline_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Создать квест")
        self.save_btn = QPushButton("Сохранить изменения")
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.shortcut_create = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_create2 = QShortcut(QKeySequence("Ctrl+Enter"), self)

        self.setLayout(layout)
        self.setMinimumWidth(600)

    def load_quest(self, quest_id: int):
        quest = self.db.get_quest(quest_id)
        if quest:
            self.current_quest_id = quest_id
            self.title_edit.setText(quest["title"])
            self.difficulty_combo.setCurrentText(quest["difficulty"])
            self.reward_spin.setValue(quest["reward"])
            self.description_edit.setPlainText(quest["description"])
            self.deadline_edit.setDateTime(QDateTime.fromString(quest["deadline"], Qt.DateFormat.ISODate))
            self.save_btn.setEnabled(False)
            self.create_btn.setEnabled(False)
            self.setWindowTitle(f"Редактор квеста: {quest['title']}")
            self._on_description_changed()

    def _connect_signals(self) -> None:
        self.title_edit.textChanged.connect(self._on_title_changed)
        self.difficulty_combo.currentTextChanged.connect(self._on_difficulty_changed)
        self.reward_spin.valueChanged.connect(self._on_reward_changed)
        self.description_edit.textChanged.connect(self._on_description_changed)
        self.deadline_edit.dateTimeChanged.connect(self._on_deadline_changed)

        self.create_btn.clicked.connect(self._on_create_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)

        self.shortcut_create.activated.connect(self._on_shortcut_create)
        self.shortcut_create2.activated.connect(self._on_shortcut_create)

    def _on_title_changed(self, text: str) -> None:
        if len(text) > 50:
            self.title_edit.setText(text[:50])
            return
        self._clear_error(self.title_edit)
        if self.current_quest_id:
            self.db.autosave_field(self.current_quest_id, "title", text)
            self.save_btn.setEnabled(True)

    def _on_difficulty_changed(self, value: str) -> None:
        if self.current_quest_id:
            self.db.autosave_field(self.current_quest_id, "difficulty", value)
            self.save_btn.setEnabled(True)

    def _on_reward_changed(self, value: int) -> None:
        if self.current_quest_id:
            self.db.autosave_field(self.current_quest_id, "reward", int(value))
            self.save_btn.setEnabled(True)

    def _on_description_changed(self) -> None:
        text = self.description_edit.toPlainText()
        words = count_words(text)
        chars = len(text)
        self.desc_counter.setText(f"Слов: {words} | Символов: {chars}")

        if words < 50:
            self._set_error(self.description_edit, f"Описание должно содержать не менее 50 слов (сейчас {words}).")
        else:
            self._clear_error(self.description_edit)

        if self.current_quest_id:
            self.db.autosave_field(self.current_quest_id, "description", text)
            self.save_btn.setEnabled(True)

    def _on_deadline_changed(self, qdt: QDateTime) -> None:
        iso = qdt.toString(Qt.DateFormat.ISODate)
        if self.current_quest_id:
            self.db.autosave_field(self.current_quest_id, "deadline", iso)
            self.save_btn.setEnabled(True)

    def _on_create_clicked(self) -> None:
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        words = count_words(description)

        if not title:
            self._set_error(self.title_edit, "Название обязательно.")
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите название квеста.")
            return

        if words < 50:
            self._set_error(self.description_edit, "Описание слишком короткое (минимум 50 слов).")
            QMessageBox.warning(self, "Ошибка", f"Описание должно содержать минимум 50 слов, сейчас {words}.")
            return

        difficulty = self.difficulty_combo.currentText()
        reward = int(self.reward_spin.value())
        deadline_iso = self.deadline_edit.dateTime().toString(Qt.DateFormat.ISODate)

        try:
            quest_id = self.db.create_quest(
                title=title,
                difficulty=difficulty,
                reward=reward,
                description=description,
                deadline=deadline_iso,
            )
            self.current_quest_id = quest_id
            self.save_btn.setEnabled(False)
            if self.gamification:
                self.gamification.award_xp(3, "Создание квеста")
            QMessageBox.information(self, "Успех", f"Квест создан (id={quest_id}). Теперь автосохранение включено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось создать квест: {e}")

    def _on_save_clicked(self) -> None:
        if not self.current_quest_id:
            QMessageBox.warning(self, "Внимание", "Сначала создайте квест (кнопка 'Создать квест').")
            return
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        words = count_words(description)
        if not title:
            self._set_error(self.title_edit, "Название обязательно.")
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите название квеста.")
            return
        if words < 50:
            self._set_error(self.description_edit, "Описание слишком короткое (минимум 50 слов).")
            QMessageBox.warning(self, "Ошибка", f"Описание должно содержать минимум 50 слов, сейчас {words}.")
            return

        fields = {
            "title": title,
            "difficulty": self.difficulty_combo.currentText(),
            "reward": int(self.reward_spin.value()),
            "description": description,
            "deadline": self.deadline_edit.dateTime().toString(Qt.DateFormat.ISODate),
        }
        try:
            self.db.update_quest(self.current_quest_id, fields)
            self.save_btn.setEnabled(False)
            QMessageBox.information(self, "Успех", "Изменения сохранены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить: {e}")

    def _on_shortcut_create(self) -> None:
        if self.current_quest_id:
            self._on_save_clicked()
        else:
            self._on_create_clicked()

    def _set_error(self, widget, message: str) -> None:
        widget.setStyleSheet("border: 1px solid red;")
        widget.setToolTip(message)

    def _clear_error(self, widget) -> None:
        widget.setStyleSheet("")
        widget.setToolTip("")

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)

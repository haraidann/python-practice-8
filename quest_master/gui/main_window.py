from __future__ import annotations
import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QListWidgetItem
)
from PyQt6.QtGui import QAction, QFontDatabase, QIcon
from PyQt6.QtCore import Qt

from quest_master.core.database import Database
from quest_master.gui.quest_wizard import QuestWizard
from quest_master.gui.map_editor import MapEditor
from quest_master.gui.gamification_panel import GamificationPanel
from quest_master.gui.export_dialog import ExportDialog
from quest_master.core.template_engine import TemplateEngine
from quest_master.core.gamification import Gamification


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuestMaster — Создание квестов")
        self.resize(800, 600)

        self.db = Database()
        self.template_engine = TemplateEngine("templates/")
        self.gamification = Gamification()

        self._load_assets()
        self._create_menu()
        self._init_dashboard()

        self.wizard: Optional[QuestWizard] = None
        self.map_editor: Optional[MapEditor] = None
        self.gamification_panel: Optional[GamificationPanel] = None

    def _load_assets(self):
        font_id = QFontDatabase.addApplicationFont("assets/fonts/uncial-antiqua.ttf")
        if font_id == -1:
            print("Warning: Font not loaded")

    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")
        new_quest_action = QAction("Новый квест", self)
        new_quest_action.triggered.connect(self._open_quest_wizard)
        file_menu.addAction(new_quest_action)
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Инструменты")
        map_action = QAction("Редактор карты", self)
        map_action.triggered.connect(self._open_map_editor)
        tools_menu.addAction(map_action)
        gamification_action = QAction("Панель достижений", self)
        gamification_action.triggered.connect(self._open_gamification_panel)
        tools_menu.addAction(gamification_action)

        export_menu = menubar.addMenu("Экспорт")
        export_act = QAction("Экспортировать текущий квест", self)
        export_act.triggered.connect(self._open_export_dialog)
        export_menu.addAction(export_act)

        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _init_dashboard(self):
        dashboard = QWidget()
        layout = QVBoxLayout()

        self.quest_list = QListWidget()
        self.quest_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.quest_list.itemDoubleClicked.connect(self._on_quest_double_clicked)
        layout.addWidget(QLabel("Список квестов:"))
        layout.addWidget(self.quest_list)

        self.export_selected_btn = QPushButton("Экспортировать выбранный квест")
        self.export_selected_btn.clicked.connect(self._export_selected_quest)
        layout.addWidget(self.export_selected_btn)

        dashboard.setLayout(layout)
        self.setCentralWidget(dashboard)

        self._refresh_quest_list()

    def _refresh_quest_list(self):
        self.quest_list.clear()
        quests = self.db.get_all_quests()
        if not quests:
            item = QListWidgetItem("Нет квестов. Создайте новый через меню 'Файл'.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.quest_list.addItem(item)
            self.export_selected_btn.setEnabled(False)
            return

        self.export_selected_btn.setEnabled(True)
        for quest in quests:
            item = QListWidgetItem(f"{quest['title']} (ID: {quest['id']}, Сложность: {quest['difficulty']})")
            item.setData(Qt.ItemDataRole.UserRole, quest['id'])
            self.quest_list.addItem(item)

    def _on_quest_double_clicked(self, item: QListWidgetItem):
        quest_id = item.data(Qt.ItemDataRole.UserRole)
        if quest_id:
            if self.wizard is None or not self.wizard.isVisible():
                self.wizard = QuestWizard(self.db, self.gamification)
            self.wizard.load_quest(quest_id)
            self.wizard.show()

    def _export_selected_quest(self):
        selected = self.quest_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Экспорт", "Выберите квест из списка.")
            return
        quest_id = selected[0].data(Qt.ItemDataRole.UserRole)
        quest = self.db.get_quest(quest_id)
        if quest:
            dlg = ExportDialog(quest, self.template_engine, self.gamification)
            dlg.exec()
        else:
            QMessageBox.warning(self, "Экспорт", "Квест не найден.")

    def _open_quest_wizard(self):
        if self.wizard is None or not self.wizard.isVisible():
            self.wizard = QuestWizard(self.db, self.gamification)
            self.wizard.show()
        self.wizard.closed.connect(self._refresh_quest_list)


    def _open_map_editor(self):
        if not self.wizard or not self.wizard.current_quest_id:
            QMessageBox.warning(self, "Карта", "Сначала создайте квест в редакторе.")
            return
        if self.map_editor is None or not self.map_editor.isVisible():
            self.map_editor = MapEditor(self.db, self.wizard.current_quest_id, self.gamification)
            self.map_editor.show()

    def _open_gamification_panel(self):
        if self.gamification_panel is None or not self.gamification_panel.isVisible():
            self.gamification_panel = GamificationPanel(self.gamification)
            self.gamification_panel.show()

    def _open_export_dialog(self):
        if not self.wizard or not self.wizard.current_quest_id:
            QMessageBox.warning(self, "Экспорт", "Откройте редактор и создайте/выберите квест.")
            return
        quest = self.db.get_quest(self.wizard.current_quest_id)
        if not quest:
            QMessageBox.warning(self, "Экспорт", "Квест не найден в базе.")
            return
        dlg = ExportDialog(quest, self.template_engine, self.gamification)
        dlg.exec()

    def _about(self):
        QMessageBox.information(
            self,
            "О программе",
            "QuestMaster\nСоздание, редактирование и экспорт игровых/учебных квестов.\n"
            "Версия 0.1.0.",
        )

    def closeEvent(self, event):
        self.db.close()
        event.accept()

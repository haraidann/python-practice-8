from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsView, QGraphicsScene, QLabel, QSlider, QInputDialog
)
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QKeySequence, QBrush, QPixmap, QFont, QShortcut
from PyQt6.QtCore import Qt, QPointF, QRectF

from quest_master.core.database import Database
from quest_master.core.gamification import Gamification


class MapEditor(QWidget):
    def __init__(self, db: Database, quest_id: int, gamification: Optional[Gamification] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор карты")
        self.setMinimumSize(900, 700)

        self.db = db
        self.quest_id = quest_id
        self.gamification = gamification

        self.current_tool = "brush"
        self.brush_size = 3
        self.brush_color = QColor("brown")
        self.items = []
        self.last_point = None

        self._build_ui()
        self._reset_state()
        self._create_shortcuts()
        self._load_locations()

    def _build_ui(self):
        layout = QVBoxLayout()

        toolbar = QHBoxLayout()
        self.btn_brush = QPushButton("Кисть (пути)")
        self.btn_brush.setCheckable(True)
        self.btn_brush.setChecked(True)
        toolbar.addWidget(self.btn_brush)

        self.btn_city = QPushButton("Город (зелёный)")
        self.btn_lair = QPushButton("Логово (красный)")
        self.btn_tavern = QPushButton("Таверна (жёлтый)")
        toolbar.addWidget(self.btn_city)
        toolbar.addWidget(self.btn_lair)
        toolbar.addWidget(self.btn_tavern)

        self.btn_text = QPushButton("Текстовая метка")
        toolbar.addWidget(self.btn_text)

        self.btn_eraser = QPushButton("Ластик (undo)")
        self.btn_eraser.setCheckable(True)
        toolbar.addWidget(self.btn_eraser)

        self.btn_load_bg = QPushButton("Загрузить фон")
        toolbar.addWidget(self.btn_load_bg)

        self.btn_save = QPushButton("Сохранить карту")
        toolbar.addWidget(self.btn_save)

        toolbar.addStretch()
        toolbar.addWidget(QLabel("Размер:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 40)
        self.size_slider.setValue(3)
        self.size_slider.setFixedWidth(150)
        toolbar.addWidget(self.size_slider)

        layout.addLayout(toolbar)


        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.scene.setBackgroundBrush(QBrush(QColor("#f4e4bc")))
        self.view = GraphicsView(self.scene, self)
        layout.addWidget(self.view)

        self.setLayout(layout)


        self.btn_brush.clicked.connect(lambda: self._select_tool("brush"))
        self.btn_city.clicked.connect(lambda: self._select_tool("city"))
        self.btn_lair.clicked.connect(lambda: self._select_tool("lair"))
        self.btn_tavern.clicked.connect(lambda: self._select_tool("tavern"))
        self.btn_text.clicked.connect(lambda: self._select_tool("text"))
        self.btn_eraser.clicked.connect(lambda: self._select_tool("eraser"))
        self.size_slider.valueChanged.connect(self._change_brush_size)
        self.btn_save.clicked.connect(self._save_canvas)
        self.btn_load_bg.clicked.connect(self._load_background)

    def _reset_state(self):

        self.last_point = None

    def _create_shortcuts(self):

        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self._undo)
        
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._save_canvas)

    def _select_tool(self, tool: str):
        self.current_tool = tool
        self.btn_brush.setChecked(tool == "brush")
        self.btn_eraser.setChecked(tool == "eraser")

    def _change_brush_size(self, value):
        self.brush_size = value

    def _add_marker(self, pos: QPointF, type_: str):
        colors = {"city": "green", "lair": "red", "tavern": "yellow"}
        color = QColor(colors[type_])
        ellipse = self.scene.addEllipse(pos.x() - 10, pos.y() - 10, 20, 20, QPen(color), QBrush(color))
        self.items.append(ellipse)
        self.db.add_location(self.quest_id, pos.x(), pos.y(), type_)

    def _add_text(self, pos: QPointF):
        text, ok = QInputDialog.getText(self, "Метка", "Введите текст:")
        if ok and text:
            item = self.scene.addText(text, QFont("Uncial Antiqua", 10))
            item.setPos(pos)
            item.setDefaultTextColor(QColor("black"))
            self.items.append(item)

    def _undo(self):
        if self.items:
            last_item = self.items.pop()
            self.scene.removeItem(last_item)
            self.db.delete_last_location(self.quest_id)

    def _load_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить фон", "", "Images (*.png *.jpg)")
        if path:
            pixmap = QPixmap(path)
            self.scene.addPixmap(pixmap.scaled(800, 600))

    def _load_locations(self):
        locations = self.db.get_locations(self.quest_id)
        for loc in locations:
            if len(loc) >= 4:
                _, x, y, type_ = loc[:4]
                self._add_marker(QPointF(x, y), type_)

    def _save_canvas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить карту", "map.png", "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        if not path:
            return
        rect = self.scene.sceneRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        if image.save(path):
            QMessageBox.information(self, "Готово", f"Карта сохранена:\n{path}")
            if self.gamification:
                self.gamification.award_xp(5, "Сохранение карты")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить.")


class GraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, editor: MapEditor, parent=None):
        super().__init__(scene, parent)
        self.editor = editor
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            if self.editor.current_tool == "brush":
                self.editor.last_point = pos
            elif self.editor.current_tool in ["city", "lair", "tavern"]:
                self.editor._add_marker(pos, self.editor.current_tool)
            elif self.editor.current_tool == "text":
                self.editor._add_text(pos)
            elif self.editor.current_tool == "eraser":
                self.editor._undo()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.editor.current_tool == "brush":
            if self.editor.last_point:
                pos = self.mapToScene(event.pos())
                pen = QPen(self.editor.brush_color, self.editor.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                line = self.editor.scene.addLine(
                    self.editor.last_point.x(), self.editor.last_point.y(),
                    pos.x(), pos.y(), pen
                )
                self.editor.items.append(line)
                self.editor.last_point = pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.editor.last_point = None
        super().mouseReleaseEvent(event)

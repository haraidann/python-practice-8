from __future__ import annotations
import os
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QComboBox, QCheckBox, QFileDialog, QMessageBox
)

from quest_master.core.template_engine import TemplateEngine
from quest_master.core.gamification import Gamification


class ExportDialog(QDialog):
    TEMPLATES = {
        "Королевский указ": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap');
        body { font-family: 'Cinzel', serif; background: linear-gradient(135deg, #f4e4bc 0%, #e8d4a0 100%);
               margin: 40px; color: #2c1810; }
        .parchment { max-width: 800px; margin: 0 auto; background: #fdf8e8; padding: 60px;
                     border: 3px solid #8B0000; box-shadow: 0 0 30px rgba(139, 0, 0, 0.3); }
        .crown { text-align: center; font-size: 60px; margin-bottom: 20px; color: #FFD700; }
        h1 { text-align: center; color: #8B0000; font-size: 42px; text-transform: uppercase;
             letter-spacing: 3px; border-bottom: 3px double #8B0000; padding-bottom: 15px; }
        .section { margin: 25px 0; line-height: 1.8; }
        .label { font-weight: 700; color: #8B0000; text-transform: uppercase; font-size: 16px; }
        .value { margin-left: 10px; font-size: 18px; }
        .difficulty-badge { display: inline-block; padding: 5px 15px; background: #8B0000;
                           color: #FFD700; border-radius: 5px; font-weight: bold; }
        .description { background: rgba(255, 255, 255, 0.5); padding: 20px;
                      border-left: 5px solid #8B0000; margin: 30px 0; font-size: 16px; }
        .seal { width: 150px; height: 150px; border: 8px solid #8B0000; border-radius: 50%;
               display: inline-flex; align-items: center; justify-content: center;
               background: radial-gradient(circle, #FFD700 0%, #FFA500 100%);
               font-size: 14px; font-weight: bold; color: #8B0000; margin: 30px auto; }
        .qr-section { text-align: center; margin-top: 30px; padding: 20px;
                     background: rgba(255,255,255,0.7); border: 2px dashed #8B0000; }
        .qr-section img { max-width: 200px; }
    </style>
</head>
<body>
    <div class="parchment">
        <div class="crown">👑</div>
        <h1>Королевский Указ</h1>
        <div class="section"><span class="label">Квест:</span><span class="value">{{ quest.title }}</span></div>
        <div class="section"><span class="label">Сложность:</span><span class="difficulty-badge">{{ quest.difficulty }}</span></div>
        <div class="section"><span class="label">Награда:</span><span class="value">{{ quest.reward }} золотых</span></div>
        <div class="section"><span class="label">Дедлайн:</span><span class="value">{{ quest.deadline }}</span></div>
        <div class="description"><p><strong>Описание:</strong></p><p>{{ quest.description }}</p></div>
        {% if qr_img_data %}<div class="qr-section"><p><strong>QR-код:</strong></p><img src="{{ qr_img_data }}" /></div>{% endif %}
        <center><div class="seal">КОРОЛЕВСКАЯ<br>ПЕЧАТЬ<br>⚜</div></center>
        <center style="margin-top:40px;font-size:12px;color:#666;">Издано {{ now }}</center>
    </div>
</body>
</html>""",
        
        "Контракт гильдии": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;700&display=swap');
        body { font-family: 'Roboto Slab', serif; background: #f4e4bc; padding: 40px; color: #1a1a1a; }
        .contract { max-width: 900px; margin: 0 auto; background: #fff; padding: 50px;
                   border: 5px double #8B0000; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .header { text-align: center; border-bottom: 3px solid #8B0000; padding-bottom: 30px; margin-bottom: 40px; }
        .guild-logo { font-size: 70px; }
        h1 { color: #8B0000; font-size: 36px; text-transform: uppercase; letter-spacing: 2px; }
        .field { margin: 25px 0; display: grid; grid-template-columns: 200px 1fr; gap: 15px; }
        .field-label { font-weight: 700; color: #8B0000; text-transform: uppercase; font-size: 13px; }
        .field-value { background: #f9f9f9; padding: 10px 15px; border-left: 4px solid #8B0000; font-size: 16px; }
        .difficulty-indicator { display: inline-block; padding: 8px 20px; background: #8B0000;
                               color: white; border-radius: 3px; font-weight: bold; }
        .reward-box { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                     padding: 15px; text-align: center; font-size: 28px; font-weight: bold;
                     color: #8B0000; border: 3px solid #8B0000; }
        .description-section { margin: 40px 0; }
        .description-title { font-weight: 700; color: #8B0000; text-transform: uppercase;
                            font-size: 18px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        .description-text { background: #f9f9f9; padding: 25px; border: 1px solid #ddd;
                           font-size: 15px; line-height: 1.9; }
        .guild-seal { width: 120px; height: 120px; border: 5px solid #8B0000; border-radius: 50%;
                     display: flex; align-items: center; justify-content: center; margin: 30px auto;
                     background: #FFD700; font-weight: bold; font-size: 12px; color: #8B0000; }
        .qr-section { text-align: center; margin: 30px 0; padding: 20px; background: #f9f9f9; border: 2px solid #ddd; }
        .qr-section img { max-width: 180px; }
    </style>
</head>
<body>
    <div class="contract">
        <div class="header">
            <div class="guild-logo">⚔️</div>
            <h1>Контракт Гильдии Приключенцев</h1>
            <div style="font-size:14px;color:#666;">Контракт №{{ quest.id }}</div>
        </div>
        <div class="field"><div class="field-label">Название:</div><div class="field-value">{{ quest.title }}</div></div>
        <div class="field"><div class="field-label">Сложность:</div><div class="field-value"><span class="difficulty-indicator">{{ quest.difficulty }}</span></div></div>
        <div class="field"><div class="field-label">Награда:</div><div class="field-value"><div class="reward-box">{{ quest.reward }} 💰</div></div></div>
        <div class="field"><div class="field-label">Дедлайн:</div><div class="field-value">{{ quest.deadline }}</div></div>
        <div class="description-section">
            <div class="description-title">📜 Описание</div>
            <div class="description-text">{{ quest.description }}</div>
        </div>
        {% if qr_img_data %}<div class="qr-section"><p><strong>QR-код контракта:</strong></p><img src="{{ qr_img_data }}" /></div>{% endif %}
        <div class="guild-seal">⚔️<br>ПЕЧАТЬ<br>ГИЛЬДИИ</div>
        <center style="margin-top:40px;font-size:11px;color:#999;">{{ now }}<br>Гильдия Приключенцев</center>
    </div>
</body>
</html>""",
        
        "Древний свиток": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Oldenburg&display=swap');
        body { font-family: 'Oldenburg', cursive; background: #1a1410; padding: 40px; color: #d4c5a0; }
        .scroll { max-width: 850px; margin: 0 auto; background: linear-gradient(90deg, #2a1f15 0%, #3d2f1f 50%, #2a1f15 100%);
                 padding: 60px 50px; border: 3px solid #4a3520; box-shadow: inset 0 0 50px rgba(0,0,0,0.5); }
        .runes { text-align: center; font-size: 30px; color: #8B7355; letter-spacing: 15px; opacity: 0.7; }
        .ancient-symbol { text-align: center; font-size: 60px; color: #d4a574; margin: 20px 0; }
        h1 { text-align: center; color: #d4a574; font-size: 48px; text-transform: uppercase;
             letter-spacing: 5px; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
        .property { margin: 25px 0; padding: 15px; background: rgba(139, 115, 85, 0.1); border-left: 4px solid #8B7355; }
        .property-label { color: #d4a574; font-size: 18px; text-transform: uppercase; letter-spacing: 2px; }
        .property-value { color: #c4b5a0; font-size: 16px; padding-left: 15px; margin-top: 8px; }
        .difficulty-orb { display: inline-block; padding: 10px 25px; background: radial-gradient(circle, #4a1f1f 0%, #2a0f0f 100%);
                         color: #ff6b6b; border: 2px solid #8B7355; border-radius: 20px; font-weight: bold; }
        .reward-glow { display: inline-block; padding: 15px 30px; color: #FFD700; font-size: 24px; font-weight: bold;
                      background: radial-gradient(circle, #3d2f1f 0%, #2a1f15 100%); border: 2px solid #8B7355; }
        .prophecy { margin: 40px 0; padding: 30px; background: rgba(0,0,0,0.4); border: 2px double #8B7355; }
        .prophecy-title { text-align: center; color: #d4a574; font-size: 24px; text-transform: uppercase; letter-spacing: 3px; }
        .prophecy-text { color: #c4b5a0; font-size: 15px; line-height: 2; text-align: justify; margin-top: 20px; }
        .warning-seal { width: 200px; height: 200px; border: 5px solid #8B7355; border-radius: 50%;
                       display: flex; align-items: center; justify-content: center; margin: 40px auto;
                       background: radial-gradient(circle, #3d2f1f 0%, #1a1410 100%); }
        .seal-text { text-align: center; color: #d4a574; font-size: 16px; text-transform: uppercase; }
        .qr-mystery { text-align: center; margin: 40px 0; padding: 30px; background: rgba(0,0,0,0.3); border: 2px dashed #8B7355; }
        .qr-mystery img { max-width: 200px; border: 3px solid #8B7355; padding: 10px; }
    </style>
</head>
<body>
    <div class="scroll">
        <div class="runes">᚛ ᚐ ᚑ ᚒ ᚓ ᚔ ᚜</div>
        <div class="ancient-symbol">☥</div>
        <h1>{{ quest.title }}</h1>
        <center style="font-size:14px;color:#8B7355;margin:20px 0;">⟨ Свиток № {{ quest.id }} ⟩</center>
        <div class="property">
            <div class="property-label">⚔ Уровень Испытания</div>
            <div class="property-value"><span class="difficulty-orb">{{ quest.difficulty }}</span></div>
        </div>
        <div class="property">
            <div class="property-label">✦ Древняя Награда</div>
            <div class="property-value"><span class="reward-glow">{{ quest.reward }} 🜛</span></div>
        </div>
        <div class="property">
            <div class="property-label">⧗ Предначертанный Срок</div>
            <div class="property-value">{{ quest.deadline }}</div>
        </div>
        <div class="prophecy">
            <div class="prophecy-title">⟨ Пророчество ⟩</div>
            <div class="prophecy-text">{{ quest.description }}</div>
        </div>
        {% if qr_img_data %}<div class="qr-mystery"><h3 style="color:#d4a574;font-size:20px;">⟨ Мистический Знак ⟩</h3><img src="{{ qr_img_data }}" /></div>{% endif %}
        <div class="warning-seal"><div class="seal-text">Печать<br>Древних<br>☥</div></div>
        <div class="runes">᚛ ᚐ ᚑ ᚒ ᚓ ᚔ ᚜</div>
        <center style="margin-top:50px;font-size:12px;color:#8B7355;">Записано в {{ now }}</center>
    </div>
</body>
</html>"""
    }
    
    def __init__(self, quest: dict, template_engine: TemplateEngine, gamification: Optional[Gamification] = None, parent=None):
        super().__init__(parent)
        self.quest = quest
        self.te = template_engine
        self.gamification = gamification

        self.setWindowTitle(f"Экспорт квеста — {quest['title']}")
        self.setMinimumWidth(450)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel(f"<h3>Экспорт квеста: <i>{self.quest['title']}</i></h3>")
        layout.addWidget(lbl)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "DOCX"])
        layout.addWidget(QLabel("Формат файла:"))
        layout.addWidget(self.format_combo)

        self.template_combo = QComboBox()
        self.template_combo.addItems(list(self.TEMPLATES.keys()))
        layout.addWidget(QLabel("Шаблон:"))
        layout.addWidget(self.template_combo)

        self.qr_checkbox = QCheckBox("Вставить QR-код (ссылка на квест)")
        self.qr_checkbox.setChecked(True)
        layout.addWidget(self.qr_checkbox)

        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Экспортировать")
        self.btn_cancel = QPushButton("Отмена")

        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_export.clicked.connect(self._on_export)
        self.btn_cancel.clicked.connect(self.reject)

    def _on_export(self):
        fmt = self.format_combo.currentText()
        template_name = self.template_combo.currentText()
        template_str = self.TEMPLATES[template_name]

        ctx = {
            "quest": {
                "id": self.quest.get("id", "N/A"),
                "title": self.quest["title"],
                "difficulty": self.quest["difficulty"],
                "reward": self.quest["reward"],
                "description": self.quest["description"],
                "deadline": self.quest["deadline"],
            },
            "now": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }

        ext = "pdf" if fmt == "PDF" else "docx"
        default_name = f"quest_{self.quest.get('id', 'new')}_{template_name.replace(' ', '_')}.{ext}"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            default_name,
            f"{fmt} (*.{ext})"
        )

        if not save_path:
            return

        try:
            qr_link = None
            if self.qr_checkbox.isChecked():
                qr_link = f"https://example.com/quest/{self.quest.get('id', 'unknown')}"

            if fmt == "PDF":
                self.te.render_context_to_pdf(
                    template_str, ctx,
                    output_path=save_path,
                    embed_qr=qr_link
                )
            else:
                self.te.render_context_to_docx(
                    template_str, ctx,
                    output_path=save_path
                )

            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{save_path}")
            if self.gamification:
                self.gamification.award_xp(2, "Экспорт")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать файл:\n{e}")

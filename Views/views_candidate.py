import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
    QGraphicsDropShadowEffect, QScrollArea, QHBoxLayout, QLineEdit
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt, pyqtSignal
from Views.components import CircularImageAvatar, CandidateProfileModal
from Controller.controller_candidates import list_candidates


class CandidateCard(QFrame):
    """Individual candidate card for the grid."""
    view_profile_clicked = pyqtSignal(dict)  # emits candidate dict

    def __init__(self, candidate: dict):
        super().__init__()
        self.candidate = candidate
        self.setFixedSize(320, 350)
        self.setStyleSheet("""
            CandidateCard {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E5E7EB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 25)
        layout.setSpacing(12)

        # Avatar
        photo = candidate.get("photo_path")
        if photo and not os.path.isabs(photo):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photo = os.path.join(base, photo)
        
        avatar = CircularImageAvatar(photo, candidate.get("full_name", "?")[0], size=100)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name
        name_lbl = QLabel(candidate.get("full_name", "Unknown"))
        name_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #111827;")
        layout.addWidget(name_lbl)

        # Position
        role_lbl = QLabel(candidate.get("position", "Candidate"))
        role_lbl.setFont(QFont("Segoe UI", 11))
        role_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(role_lbl)

        # Slogan
        slogan_lbl = QLabel(candidate.get("slogan", ""))
        slogan_lbl.setWordWrap(True)
        slogan_lbl.setFont(QFont("Segoe UI", 10))
        slogan_lbl.setStyleSheet("color: #9CA3AF; font-style: italic;")
        slogan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_lbl.setMaximumHeight(60)
        layout.addWidget(slogan_lbl)

        layout.addStretch()

        # View Profile button
        btn = QPushButton("View Full Profile")
        btn.setFixedHeight(40)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFont(QFont("Segoe UI", 11))
        btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 2px solid #10B981;
                color: #10B981;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ECFDF5;
            }
        """)
        btn.clicked.connect(lambda: self.view_profile_clicked.emit(self.candidate))
        layout.addWidget(btn)


class CandidatesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._all_candidates = []
        self._candidates = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # White card container
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 30px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 40, 50, 40)

        # Title + search
        header_row = QHBoxLayout()
        title = QLabel("Meet the Candidates")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        header_row.addWidget(title)

        header_row.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or slogan")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 14px;
                padding: 6px 10px;
                background: #FFFFFF;
                color: #111827;
            }
            QLineEdit::placeholder { color: #9CA3AF; }
            QLineEdit:focus { border: 2px solid #10B981; }
            """
        )
        header_row.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setFixedHeight(38)
        search_btn.setMinimumWidth(90)
        search_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        search_btn.setStyleSheet(
            """
            QPushButton {
                background: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 16px;
                padding: 0 18px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }
            QPushButton:hover { background: #059669; }
            """
        )
        search_btn.clicked.connect(self._apply_filter)
        self.search_input.returnPressed.connect(self._apply_filter)
        header_row.addWidget(search_btn)

        card_layout.addLayout(header_row)
        card_layout.addSpacing(20)

        # Scrollable grid container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(25)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        scroll.setWidget(grid_container)
        card_layout.addWidget(scroll)

        layout.addWidget(card)

        # Load candidates
        self._load_candidates()

    def _load_candidates(self):
        self._all_candidates = list_candidates()
        self._candidates = list(self._all_candidates)
        self._populate_grid()

    def _apply_filter(self):
        term = (self.search_input.text() or "").strip().lower()
        if not term:
            self._candidates = list(self._all_candidates)
        else:
            def match(c):
                return term in (c.get("full_name", "").lower()) or term in (c.get("slogan", "").lower())
            self._candidates = [c for c in self._all_candidates if match(c)]
        self._populate_grid()

    def _populate_grid(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._candidates:
            placeholder = QLabel("No candidates found.")
            placeholder.setStyleSheet("color: #6B7280; font-size: 13px;")
            self.grid_layout.addWidget(placeholder, 0, 0)
            return

        row, col = 0, 0
        max_cols = 3
        for candidate in self._candidates:
            card = CandidateCard(candidate)
            card.view_profile_clicked.connect(self._show_profile)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _show_profile(self, candidate: dict):
        modal = CandidateProfileModal(candidate, parent=self)
        modal.exec()
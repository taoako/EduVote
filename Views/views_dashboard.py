import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt
from Views.components import CircularImageAvatar, VotingModal


class DashboardPage(QWidget):
    def __init__(self, user_data: dict = None):
        super().__init__()
        self.user_data = user_data or {}
        self._blocks = []  # [{election:{}, candidates:[] }]
        self._vote_handler = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # Filter tabs
        tab_row = QHBoxLayout()
        tab_row.setSpacing(12)
        self.tabs = {}
        for key, label in [("all", "All Elections"), ("active", "Active"), ("upcoming", "Upcoming"), ("ended", "Ended")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._tab_style(False))
            btn.clicked.connect(lambda checked, k=key: self._set_filter(k))
            self.tabs[key] = btn
            tab_row.addWidget(btn)
        layout.addLayout(tab_row)
        self._set_filter('all', init=True)

        # Scroll area for election cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(18)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.list_widget)

        layout.addWidget(self.scroll, 1)

    # ─── Public API ───────────────────────────────────────────────────
    def set_vote_handler(self, handler):
        self._vote_handler = handler

    def set_elections(self, blocks: list):
        self._blocks = blocks or []
        self._render()

    # ─── Internal ─────────────────────────────────────────────────────
    # Internal helpers
    def _tab_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton { background: #10B981; color: white; border: none; border-radius: 22px; padding: 10px 18px; font-weight: 600; }
            """
        return """
            QPushButton { background: #F3F4F6; color: #374151; border: none; border-radius: 22px; padding: 10px 18px; font-weight: 600; }
            QPushButton:hover { background: #E5E7EB; }
        """

    def _set_filter(self, key: str, init: bool = False):
        self._filter = key
        for k, btn in self.tabs.items():
            btn.setStyleSheet(self._tab_style(k == key))
        if not init:
            self._render()

    def _render(self):
        # clear
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for block in self._blocks:
            election = block.get('election', {})
            candidates = block.get('candidates', [])
            status = election.get('status', 'upcoming')
            if self._filter == 'active' and status != 'active':
                continue
            if self._filter == 'upcoming' and status != 'upcoming':
                continue
            if self._filter == 'ended' and status not in ('finalized', 'closed'): 
                continue

            card = QFrame()
            card.setStyleSheet("background: white; border-radius: 20px;")
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 6)
            card.setGraphicsEffect(shadow)

            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 20, 24, 20)
            cl.setSpacing(16)

            # header row
            hrow = QHBoxLayout()
            title = QLabel(election.get('title', 'Election'))
            title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
            title.setStyleSheet("color: #111827;")
            hrow.addWidget(title)

            status_chip = QLabel(status.upper())
            status_chip.setStyleSheet("""
                QLabel { padding: 6px 10px; border-radius: 12px; color: #0F5132; background: #D1FAE5; font-weight: 700; }
            """)
            hrow.addStretch()
            hrow.addWidget(status_chip)
            cl.addLayout(hrow)

            # dates
            dates = QLabel(f"Start: {election.get('start_date','-')}    End: {election.get('end_date','-')}")
            dates.setStyleSheet("color: #6B7280; font-size: 12px;")
            cl.addWidget(dates)

            # action row
            btn_text = "Enter Voting" if status == 'active' else ("Voting opens soon" if status == 'upcoming' else "Voting ended")
            btn = QPushButton(btn_text)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(40)
            btn.setEnabled(status == 'active')
            btn.setStyleSheet("""
                QPushButton { background: #10B981; color: white; border: none; border-radius: 18px; font-weight: 700; }
                QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }
            """)
            if status == 'active':
                btn.clicked.connect(lambda checked=False, e=election, c=candidates: self._open_voting_modal(e, c))
            cl.addWidget(btn)

            # Voted indicator
            voted_lbl = QLabel("Already voted")
            voted_lbl.setStyleSheet("color: #16A34A; font-weight: 700;" if election.get('user_voted') else "color: #9CA3AF;")
            voted_lbl.setVisible(bool(election.get('user_voted')))
            cl.addWidget(voted_lbl)

            self.list_layout.addWidget(card)
        self.list_layout.addStretch()

    def _open_voting_modal(self, election: dict, candidates: list):
        if not candidates:
            QMessageBox.information(self, "No Candidates", "There are no candidates available for this election.")
            return

        title = election.get("title", "Election")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved = []
        for c in candidates:
            copy = dict(c)
            photo = copy.get("photo_path")
            if photo and not os.path.isabs(photo):
                copy["photo_path"] = os.path.join(base_dir, photo)
            resolved.append(copy)

        modal = VotingModal(title, resolved, parent=self)
        modal.vote_submitted.connect(lambda cid: self._on_vote_submitted(election.get('election_id'), cid))
        modal.exec()

    def _on_vote_submitted(self, election_id: int, candidate_id: int):
        if self._vote_handler:
            self._vote_handler(election_id, candidate_id)

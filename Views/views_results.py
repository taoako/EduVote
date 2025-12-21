import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QComboBox, QScrollArea
)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt
from Views.components import CircularImageAvatar
from Controller.controller_elections import get_election_results
from Models.model_db import Database


class ProgressBar(QWidget):
    def __init__(self, color_hex, percentage):
        super().__init__()
        self.setFixedHeight(12)
        self.color = QColor(color_hex)
        self.pct = percentage

    def paintEvent(self, e):
        p = QPainter(self);
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Background
        p.setBrush(QBrush(QColor("#F3F4F6")));
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 6, 6)
        # Fill
        p.setBrush(QBrush(self.color))
        w = int(self.width() * (self.pct / 100))
        p.drawRoundedRect(0, 0, w, 12, 6, 6)


class ResultsPage(QWidget):
    def __init__(self, user_data: dict | None = None):
        super().__init__()
        self.user_data = user_data or {}
        self.avatar_widget = None
        self.elections = []
        self.election_selector = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # White card
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 30px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 45, 50, 45)

        # Header row with selector
        header_row = QHBoxLayout()

        selector_label = QLabel("Select Election")
        selector_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        selector_label.setStyleSheet("color: #111827;")

        self.election_selector = QComboBox()
        self.election_selector.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: #FFFFFF;
                color: #111827;
                min-width: 280px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                color: #111827;
                background: #FFFFFF;
                selection-background-color: #DBEAFE;
            }
        """)
        self.election_selector.currentIndexChanged.connect(self._on_select_changed)

        header_row.addWidget(selector_label)
        header_row.addWidget(self.election_selector)
        header_row.addStretch()
        card_layout.addLayout(header_row)
        card_layout.addSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        
        self.title_label = QLabel("Election Results")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #111827;")
        
        self.badge = QLabel(" NO DATA ")
        self.badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.badge.setStyleSheet("""
            background-color: #F3F4F6;
            color: #6B7280;
            border-radius: 8px;
            padding: 4px 12px;
        """)
        self.badge.setFixedHeight(24)
        
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.badge)
        title_row.addStretch()
        card_layout.addLayout(title_row)
        card_layout.addSpacing(20)

        # Winner banner
        banner = QFrame()
        banner.setStyleSheet("background-color: #ECFDF5; border-radius: 20px;")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(40, 30, 40, 30)
        banner_layout.setSpacing(25)
        self.banner_layout = banner_layout

        # Trophy icon
        trophy = QLabel("🏆")
        trophy.setFont(QFont("Segoe UI", 45))
        trophy.setFixedSize(70, 70)
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(trophy)

        self.winner_info = QWidget()
        info_layout = QVBoxLayout(self.winner_info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        winner_label = QLabel("Winner")
        winner_label.setFont(QFont("Segoe UI", 11))
        winner_label.setStyleSheet("color: #6B7280;")

        self.winner_name = QLabel("No election")
        self.winner_name.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.winner_name.setStyleSheet("color: #111827;")

        self.winner_votes = QLabel("")
        self.winner_votes.setFont(QFont("Segoe UI", 11))
        self.winner_votes.setStyleSheet("color: #6B7280;")

        info_layout.addWidget(winner_label)
        info_layout.addWidget(self.winner_name)
        info_layout.addWidget(self.winner_votes)

        banner_layout.addWidget(self.winner_info)
        banner_layout.addStretch()
        card_layout.addWidget(banner)
        card_layout.addSpacing(35)

        self.results_container = QVBoxLayout()
        self.results_container.setSpacing(20)

        # Wrap results container in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setLayout(self.results_container)
        scroll_area.setWidget(scroll_content)

        card_layout.addWidget(scroll_area)
        card_layout.addStretch()
        layout.addWidget(card)

        self._load_elections()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.deleteLater()
            if child_layout:
                self._clear_layout(child_layout)

    def _set_avatar(self, photo_path: str, initial: str):
        if self.avatar_widget:
            self.avatar_widget.setParent(None)
            self.banner_layout.removeWidget(self.avatar_widget)
        avatar = CircularImageAvatar(photo_path, initial or "?", size=80)
        self.avatar_widget = avatar
        self.banner_layout.insertWidget(1, avatar)

    def _render_placeholder(self):
        self._clear_layout(self.results_container)
        if self.avatar_widget:
            self.banner_layout.removeWidget(self.avatar_widget)
            self.avatar_widget.deleteLater()
            self.avatar_widget = None
        placeholder = QLabel("No active results to show.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #6B7280; font-size: 13px;")
        self.results_container.addWidget(placeholder)

    def refresh(self, election=None):
        if election is None:
            election = self._get_default_election()

        candidates_sorted = []
        if election:
            from Controller.controller_candidates import get_candidates_for_election
            candidates = get_candidates_for_election(election.get("election_id"))
            if candidates:
                candidates_sorted = sorted(candidates, key=lambda c: c.get("vote_count", 0), reverse=True)

        if not election or not candidates_sorted:
            self.title_label.setText("Election Results")
            self.badge.setText(" NO DATA ")
            self.badge.setStyleSheet("background-color: #F3F4F6; color: #6B7280; border-radius: 8px; padding: 4px 12px;")
            self.winner_name.setText("No election available")
            self.winner_votes.setText("")
            self._render_placeholder()
            return

        total_votes = sum(c.get("vote_count", 0) for c in candidates_sorted)
        winner = candidates_sorted[0]

        self.title_label.setText(f"Election Results: {election.get('title', 'Election')}")
        status = (election.get("status") or "active").upper()
        status_bg = "#D1FAE5" if status == "FINALIZED" else "#DBEAFE"
        status_fg = "#065F46" if status == "FINALIZED" else "#1D4ED8"
        self.badge.setText(f" {status} ")
        self.badge.setStyleSheet(f"background-color: {status_bg}; color: {status_fg}; border-radius: 8px; padding: 4px 12px;")

        photo = winner.get("photo_path")
        if photo and not os.path.isabs(photo):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photo = os.path.join(base, photo)
        self._set_avatar(photo, winner.get("full_name", "?")[0:1])

        self.winner_name.setText(winner.get("full_name", "Unknown"))
        self.winner_votes.setText(f"Total Votes: {winner.get('vote_count', 0)}")

        self._clear_layout(self.results_container)

        for idx, candidate in enumerate(candidates_sorted):
            votes = candidate.get("vote_count", 0)
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0

            result_row = QVBoxLayout()
            result_row.setSpacing(8)

            top_row = QHBoxLayout()

            photo = candidate.get("photo_path")
            if photo and not os.path.isabs(photo):
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                photo = os.path.join(base, photo)

            avatar_small = CircularImageAvatar(photo, candidate.get("full_name", "?")[0], size=40)
            top_row.addWidget(avatar_small)

            name = QLabel(candidate.get("full_name", "Unknown"))
            name.setFont(QFont("Segoe UI", 13))
            name.setStyleSheet("color: #111827;")
            top_row.addWidget(name)

            top_row.addStretch()

            pct_label = QLabel(f"{percentage:.0f}%")
            pct_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            pct_label.setStyleSheet("color: #6B7280;")
            top_row.addWidget(pct_label)

            result_row.addLayout(top_row)

            bar_color = "#10B981" if idx == 0 else "#CBD5E1"
            progress = ProgressBar(bar_color, percentage)
            result_row.addWidget(progress)

            votes_label = QLabel(f"{votes} votes")
            votes_label.setFont(QFont("Segoe UI", 10))
            votes_label.setStyleSheet("color: #9CA3AF;")
            result_row.addWidget(votes_label)

            self.results_container.addLayout(result_row)
            self.results_container.addSpacing(10)

    def _get_default_election(self):
        if not self.elections:
            return None
        active = [e for e in self.elections if (e.get("status") or "").lower() == "active"]
        return active[0] if active else self.elections[0]

    def _on_select_changed(self, idx: int):
        if idx < 0 or idx >= len(self.elections):
            return
        election = self.elections[idx]
        self.refresh(election)

    def _load_elections(self):
        user_id = self.user_data.get("id") or self.user_data.get("user_id")
        db = Database()
        self.elections = db.get_user_allowed_elections(user_id) if user_id else db.get_all_elections()

        self.election_selector.blockSignals(True)
        self.election_selector.clear()
        for e in self.elections:
            start = e.get("start_date")
            end = e.get("end_date")
            date_str = "" if not start and not end else f" ({start} - {end})"
            status = (e.get("status") or "").upper()
            label = f"{e.get('title', 'Election')} [{status}]{date_str}"
            self.election_selector.addItem(label)
        self.election_selector.blockSignals(False)

        default_election = self._get_default_election()
        if default_election:
            default_idx = self.elections.index(default_election)
            self.election_selector.setCurrentIndex(default_idx)
            self.refresh(default_election)
        else:
            self.refresh(None)
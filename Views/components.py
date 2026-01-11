from PyQt6.QtWidgets import (
    QWidget, QPushButton, QApplication, QStyle, QLabel, QVBoxLayout, QHBoxLayout,
    QDialog, QGridLayout, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPainterPath, QFont, QCursor, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import os


class CircularImageAvatar(QLabel):
    """Circular avatar that displays an image file, or falls back to initials."""
    def __init__(self, image_path: str = None, fallback_initial: str = "?", size: int = 80, fallback_color: str = "#22C55E"):
        super().__init__()
        self.setFixedSize(size, size)
        self._size = size
        self._fallback_initial = fallback_initial
        self._fallback_color = QColor(fallback_color)
        self._pixmap = None

        if image_path and os.path.exists(image_path):
            pm = QPixmap(image_path)
            if not pm.isNull():
                self._pixmap = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clip to circle
        path = QPainterPath()
        path.addEllipse(0, 0, self._size, self._size)
        painter.setClipPath(path)

        if self._pixmap:
            x = max(0, (self._pixmap.width() - self._size) // 2)
            y = max(0, (self._pixmap.height() - self._size) // 2)
            painter.drawPixmap(0, 0, self._pixmap, x, y, self._size, self._size)
        else:
            painter.setBrush(QBrush(self._fallback_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self._size, self._size)
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Segoe UI", int(self._size * 0.35), QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._fallback_initial)

class CandidateProfileModal(QDialog):
    """Modal to show detailed candidate profile (matches the reference style)."""

    def __init__(self, candidate: dict, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(600, 520)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 22px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(14)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(
            """
            QPushButton { background: transparent; border: none; color: #6B7280; font-size: 16px; }
            QPushButton:hover { color: #111827; }
            """
        )
        close_btn.clicked.connect(self.reject)

        top_row = QHBoxLayout()
        top_row.addStretch()
        top_row.addWidget(close_btn)
        layout.addLayout(top_row)

        # make the large content scrollable to avoid clipping on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Resolve relative photo paths so avatars always render
        photo_path = candidate.get("photo_path")
        if photo_path and not os.path.isabs(photo_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            photo_path = os.path.join(base_dir, photo_path)

        full_name = candidate.get("full_name", "Unknown")
        avatar_initial = full_name[:1] or "?"
        avatar = CircularImageAvatar(photo_path, avatar_initial, size=90)
        content_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(full_name)
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #111827;")
        content_layout.addWidget(name_lbl)

        position_lbl = QLabel(candidate.get("position", "Candidate"))
        position_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        position_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        position_lbl.setStyleSheet("color: #10B981;")
        content_layout.addWidget(position_lbl)

        slogan = candidate.get("slogan", "")
        slogan_lbl = QLabel(f'"{slogan}"' if slogan else "")
        slogan_lbl.setFont(QFont("Segoe UI", 10))
        slogan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_lbl.setStyleSheet("color: #9CA3AF; font-style: italic;")
        slogan_lbl.setWordWrap(True)
        content_layout.addWidget(slogan_lbl)

        about_title = QLabel("About")
        about_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        about_title.setStyleSheet("color: #111827;")
        content_layout.addWidget(about_title)

        about_text = QLabel(candidate.get("bio") or "No bio provided.")
        about_text.setFont(QFont("Segoe UI", 10))
        about_text.setStyleSheet("color: #4B5563;")
        about_text.setWordWrap(True)
        content_layout.addWidget(about_text)

        contact_title = QLabel("Contact Information")
        contact_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        contact_title.setStyleSheet("color: #111827; margin-top: 6px;")
        content_layout.addWidget(contact_title)

        email = candidate.get("email", "-")
        phone = candidate.get("phone", "-")

        contact_email = QLabel(f"✉  {email}")
        contact_email.setFont(QFont("Segoe UI", 10))
        contact_email.setStyleSheet("color: #10B981;")
        content_layout.addWidget(contact_email)

        contact_phone = QLabel(f"☎  {phone}")
        contact_phone.setFont(QFont("Segoe UI", 10))
        contact_phone.setStyleSheet("color: #10B981;")
        content_layout.addWidget(contact_phone)

        platform_title = QLabel("Campaign Platform")
        platform_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        platform_title.setStyleSheet("color: #111827; margin-top: 6px;")
        content_layout.addWidget(platform_title)

        platform_text = candidate.get("platform") or ""
        bullet_sep = "|" if "|" in platform_text else "\n"
        bullets = [b.strip() for b in platform_text.split(bullet_sep) if b.strip()]
        if not bullets:
            placeholder = QLabel("No platform provided.")
            placeholder.setFont(QFont("Segoe UI", 10))
            placeholder.setStyleSheet("color: #9CA3AF;")
            content_layout.addWidget(placeholder)
        else:
            for item_clean in bullets:
                item_lbl = QLabel(f"•  {item_clean}")
                item_lbl.setFont(QFont("Segoe UI", 10))
                item_lbl.setStyleSheet("color: #10B981;")
                content_layout.addWidget(item_lbl)

        content_layout.addStretch()

        close_bottom = QPushButton("Close")
        close_bottom.setFixedHeight(42)
        close_bottom.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_bottom.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_bottom.setStyleSheet(
            """
            QPushButton { background-color: #10B981; color: white; border: none; border-radius: 23px; }
            QPushButton:hover { background-color: #059669; }
            """
        )
        close_bottom.clicked.connect(self.accept)
        content_layout.addWidget(close_bottom)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        outer.addWidget(card)


class CandidateCard(QFrame):
    """Card used inside the voting modal to pick a candidate."""

    clicked = pyqtSignal()

    def __init__(self, candidate_id: int, name: str, slogan: str, photo_path: str | None, position: str | None = None):
        super().__init__()
        self.candidate_id = candidate_id
        self._base_style = (
            "CandidateCard { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 18px; }"
            "CandidateCard:hover { border: 1px solid #10B981; box-shadow: 0 10px 25px rgba(0,0,0,0.06); }"
        )
        self._selected_style = (
            "CandidateCard { background: #ECFDF5; border: 2px solid #10B981; border-radius: 18px; }"
        )
        self.setStyleSheet(self._base_style)
        self.setFixedSize(220, 240)

        # Resolve relative photos to absolute paths
        resolved_photo = photo_path
        if resolved_photo and not os.path.isabs(resolved_photo):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resolved_photo = os.path.join(base_dir, resolved_photo)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(10)

        avatar = CircularImageAvatar(resolved_photo, name[0] if name else "?", size=70)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(name or "Unknown")
        name_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #111827;")
        layout.addWidget(name_lbl)

        pos_text = (position or "").strip()
        if pos_text:
            pos_lbl = QLabel(pos_text)
            pos_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            pos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pos_lbl.setStyleSheet("color: #10B981;")
            layout.addWidget(pos_lbl)

        slogan_lbl = QLabel(slogan or "")
        slogan_lbl.setFont(QFont("Segoe UI", 10))
        slogan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_lbl.setStyleSheet("color: #6B7280;")
        slogan_lbl.setWordWrap(True)
        slogan_lbl.setMaximumHeight(60)
        layout.addWidget(slogan_lbl)

        layout.addStretch()

        choose_lbl = QLabel("Select")
        choose_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        choose_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        choose_lbl.setStyleSheet("color: #10B981;")
        layout.addWidget(choose_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, is_selected: bool):
        self.setStyleSheet(self._selected_style if is_selected else self._base_style)


class VotingModal(QDialog):
    """Modal dialog for casting a vote."""
    vote_submitted = pyqtSignal(int)  # emits candidate_id

    def __init__(self, election_title: str, candidates: list, parent=None):
        """
        candidates: list of dicts with keys: candidate_id, full_name, slogan, photo_path
        """
        super().__init__(parent)
        self.setWindowTitle("Cast Your Vote")
        self.setModal(True)
        self.setMinimumSize(750, 550)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 16px;")

        self._cards: list[CandidateCard] = []
        self._selected_candidate_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # Header
        header = QLabel("Cast Your Vote")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #111827;")
        layout.addWidget(header)

        subtitle = QLabel(f"Select a candidate to vote for {election_title}:")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #6B7280;")
        layout.addWidget(subtitle)

        # Scrollable grid of candidate cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(5, 5, 5, 5)

        row, col = 0, 0
        max_cols = 3
        for c in candidates:
            card = CandidateCard(
                candidate_id=c.get("candidate_id"),
                name=c.get("full_name", "Unknown"),
                slogan=c.get("slogan", ""),
                photo_path=c.get("photo_path"),
                position=c.get("position")
            )
            card.clicked.connect(lambda cid=c.get("candidate_id"): self._on_card_clicked(cid))
            self._cards.append(card)
            grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        scroll.setWidget(grid_container)
        layout.addWidget(scroll, 1)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setMinimumWidth(180)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFont(QFont("Segoe UI", 12))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        self.submit_btn = QPushButton("☑  Submit Vote")
        self.submit_btn.setFixedHeight(50)
        self.submit_btn.setMinimumWidth(220)
        self.submit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.submit_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._on_submit)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.submit_btn)
        layout.addLayout(btn_row)

    def _on_card_clicked(self, candidate_id: int):
        self._selected_candidate_id = candidate_id
        for card in self._cards:
            card.set_selected(card.candidate_id == candidate_id)
        self.submit_btn.setEnabled(True)

    def _on_submit(self):
        if self._selected_candidate_id is not None:
            self.vote_submitted.emit(self._selected_candidate_id)
            self.accept()


class CircularAvatar(QWidget):
    def __init__(self, color_hex, initial, size=80):
        super().__init__()
        self.setFixedSize(size, size)
        self.color = QColor(color_hex)
        self.initial = initial

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(path)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", int(self.height() * 0.35), QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.initial)


class SidebarButton(QPushButton):
    """Simple pill-style sidebar button to avoid layout glitches."""
    def __init__(self, text, icon_label):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(56)
        self.setCheckable(False)

        # Combine icon and text with spacing
        self.icon_label = icon_label
        self.text_label = text
        self._apply_text()

        self.base_style = """
            QPushButton {
                text-align: left;
                padding: 0 20px;
                padding-left: 22px;
                border-radius: 28px;
                border: none;
                background: transparent;
                color: #374151;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #F0FDF4;
            }
        """

        self.active_style = """
            QPushButton {
                text-align: left;
                padding: 0 20px;
                padding-left: 22px;
                border-radius: 28px;
                border: none;
                background: #10B981;
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }
        """

        self.setStyleSheet(self.base_style)

    def _apply_text(self):
        # Use narrow space between icon and label
        self.setText(f"{self.icon_label}   {self.text_label}")

    def set_active(self, is_active: bool):
        self.setStyleSheet(self.active_style if is_active else self.base_style)


class PositionCandidateCard(QFrame):
    """Candidate card for ballot voting - single selection per position."""
    clicked = pyqtSignal()

    def __init__(self, candidate_id: int, name: str, slogan: str, photo_path: str | None):
        super().__init__()
        self.candidate_id = candidate_id
        self._selected = False
        self._disabled = False
        self.setFixedSize(180, 200)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

        # Resolve relative photos
        resolved_photo = photo_path
        if resolved_photo and not os.path.isabs(resolved_photo):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resolved_photo = os.path.join(base_dir, resolved_photo)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(8)

        # Avatar
        avatar = CircularImageAvatar(resolved_photo, name[0] if name else "?", size=60)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name
        name_lbl = QLabel(name or "Unknown")
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #111827; background: transparent;")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # Slogan
        slogan_lbl = QLabel(slogan or "")
        slogan_lbl.setFont(QFont("Segoe UI", 9))
        slogan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_lbl.setStyleSheet("color: #6B7280; background: transparent;")
        slogan_lbl.setWordWrap(True)
        slogan_lbl.setMaximumHeight(40)
        layout.addWidget(slogan_lbl)

        layout.addStretch()

        # Checkmark indicator
        self.check_label = QLabel("✓ Selected")
        self.check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.check_label.setStyleSheet("color: #10B981; background: transparent;")
        self.check_label.setVisible(False)
        layout.addWidget(self.check_label)

    def _update_style(self):
        if self._disabled:
            self.setStyleSheet("""
                PositionCandidateCard {
                    background: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                }
            """)
            if hasattr(self, 'check_label'):
                self.check_label.setVisible(False)
            return
        if self._selected:
            self.setStyleSheet("""
                PositionCandidateCard {
                    background: #ECFDF5;
                    border: 2px solid #10B981;
                    border-radius: 16px;
                }
            """)
            if hasattr(self, 'check_label'):
                self.check_label.setVisible(True)
        else:
            self.setStyleSheet("""
                PositionCandidateCard {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                }
                PositionCandidateCard:hover {
                    border: 1px solid #10B981;
                }
            """)
            if hasattr(self, 'check_label'):
                self.check_label.setVisible(False)

    def mousePressEvent(self, event):
        if self._disabled:
            return
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, is_selected: bool):
        self._selected = is_selected
        self._update_style()

    def set_disabled(self, disabled: bool):
        self._disabled = bool(disabled)
        self.setCursor(Qt.CursorShape.ArrowCursor if self._disabled else QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected


class PositionSection(QFrame):
    """Section for a single position with multiple candidate options."""
    selection_changed = pyqtSignal(int, int)  # position_id, candidate_id (or -1 if none)

    def __init__(self, position_id: int, position_title: str, candidates: list, *, locked: bool = False):
        super().__init__()
        self.position_id = position_id
        self.position_title = position_title
        self._cards = []
        self._selected_candidate_id = None
        self._locked = bool(locked)

        self.setStyleSheet("""
            PositionSection {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Position header
        header = QHBoxLayout()
        title_lbl = QLabel(position_title)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #111827; background: transparent;")
        header.addWidget(title_lbl)

        header.addStretch()

        self.status_label = QLabel("Select one candidate")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #9CA3AF; background: transparent;")
        header.addWidget(self.status_label)

        layout.addLayout(header)

        # Candidates grid
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        row, col = 0, 0
        max_cols = 4

        # Add an abstain card (candidate_id=0) so users can submit a blank ballot for this position.
        abstain = PositionCandidateCard(
            candidate_id=0,
            name="Abstain",
            slogan="No selection for this position",
            photo_path=None,
        )
        abstain.clicked.connect(lambda: self._on_card_clicked(0))
        self._cards.append(abstain)
        grid_layout.addWidget(abstain, row, col)
        col += 1
        if col >= max_cols:
            col = 0
            row += 1

        for c in candidates:
            card = PositionCandidateCard(
                candidate_id=c.get("candidate_id"),
                name=c.get("full_name", "Unknown"),
                slogan=c.get("slogan", ""),
                photo_path=c.get("photo_path")
            )
            card.clicked.connect(lambda cid=c.get("candidate_id"): self._on_card_clicked(cid))
            self._cards.append(card)
            grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addWidget(grid_container)

        if self._locked:
            self.status_label.setText("✓ Already voted")
            self.status_label.setStyleSheet("color: #10B981; font-weight: bold; background: transparent;")
            for card in self._cards:
                card.set_disabled(True)

    def _on_card_clicked(self, candidate_id: int):
        if self._locked:
            return
        self._selected_candidate_id = candidate_id
        for card in self._cards:
            card.set_selected(card.candidate_id == candidate_id)
        self.status_label.setText("✓ Selected")
        self.status_label.setStyleSheet("color: #10B981; font-weight: bold; background: transparent;")
        self.selection_changed.emit(self.position_id, candidate_id)

    def get_selected_candidate_id(self) -> int | None:
        return self._selected_candidate_id

    def is_completed(self) -> bool:
        return self._locked or (self._selected_candidate_id is not None)

    def is_locked(self) -> bool:
        return self._locked


class BallotVotingModal(QDialog):
    """Ballot-style voting modal with multiple positions."""
    ballot_submitted = pyqtSignal(list)  # emits list of {"position_id": int, "candidate_id": int}

    def __init__(self, election_title: str, positions_data: list, voted_position_ids: list[int] | None = None, parent=None):
        """
        positions_data: list of {
            "position": {"position_id": int, "title": str},
            "candidates": [{"candidate_id": int, "full_name": str, "slogan": str, "photo_path": str}, ...]
        }
        """
        super().__init__(parent)
        self.setWindowTitle("Cast Your Ballot")
        self.setModal(True)
        self.setMinimumSize(850, 650)
        self.setStyleSheet("background-color: #F9FAFB;")

        self._position_sections = []
        self._total_positions = len(positions_data)
        self._voted_position_ids = set(voted_position_ids or [])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #FFFFFF;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 25, 30, 20)
        header_layout.setSpacing(12)

        title = QLabel("Cast Your Ballot")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        header_layout.addWidget(title)

        subtitle = QLabel(f"Vote for {election_title}")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #6B7280;")
        header_layout.addWidget(subtitle)

        # Progress tracker
        progress_container = QHBoxLayout()
        progress_container.setSpacing(12)

        self.progress_label = QLabel(f"Progress: 0/{self._total_positions} positions selected")
        self.progress_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #374151;")
        progress_container.addWidget(self.progress_label)

        progress_container.addStretch()

        # Progress bar visual
        self.progress_bar = QFrame()
        self.progress_bar.setFixedSize(200, 8)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #E5E7EB;
                border-radius: 4px;
            }
        """)
        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setGeometry(0, 0, 0, 8)
        self.progress_fill.setStyleSheet("""
            QFrame {
                background-color: #10B981;
                border-radius: 4px;
            }
        """)
        progress_container.addWidget(self.progress_bar)

        header_layout.addLayout(progress_container)
        layout.addWidget(header_widget)

        # Scrollable content for positions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        for pos_data in positions_data:
            pos = pos_data.get("position", {})
            candidates = pos_data.get("candidates", [])
            if not candidates:
                continue

            pos_id = pos.get("position_id")
            locked = (pos_id in self._voted_position_ids)

            section = PositionSection(
                position_id=pos_id,
                position_title=pos.get("title", "Position"),
                candidates=candidates,
                locked=locked
            )
            section.selection_changed.connect(self._on_selection_changed)
            self._position_sections.append(section)
            content_layout.addWidget(section)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)

        # Footer with buttons
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background-color: #FFFFFF;")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(30, 20, 30, 25)
        footer_layout.setSpacing(15)

        # Warning label
        self.warning_label = QLabel("⚠ Please select a candidate for each position before submitting.")
        self.warning_label.setFont(QFont("Segoe UI", 10))
        self.warning_label.setStyleSheet("color: #F59E0B;")
        footer_layout.addWidget(self.warning_label)

        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFont(QFont("Segoe UI", 12))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        self.submit_btn = QPushButton("☑  Submit Ballot")
        self.submit_btn.setFixedHeight(50)
        self.submit_btn.setMinimumWidth(180)
        self.submit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.submit_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._on_submit)

        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(self.submit_btn)
        layout.addWidget(footer_widget)

        self._update_progress()

    def _on_selection_changed(self, position_id: int, candidate_id: int):
        self._update_progress()

    def _update_progress(self):
        completed = sum(1 for s in self._position_sections if s.is_completed())
        total = len(self._position_sections)
        remaining = sum(1 for s in self._position_sections if not s.is_locked())
        remaining_done = sum(1 for s in self._position_sections if (not s.is_locked()) and s.get_selected_candidate_id() is not None)
        self.progress_label.setText(f"Progress: {completed}/{total} positions completed")

        # Update progress bar
        if total > 0:
            fill_width = int(200 * completed / total)
            self.progress_fill.setGeometry(0, 0, fill_width, 8)

        # Enable submit if all remaining (not-yet-voted) positions have a selection/abstain.
        all_remaining_completed = (remaining == 0) or (remaining_done == remaining)
        self.submit_btn.setEnabled(all_remaining_completed and remaining > 0)
        if remaining == 0:
            self.warning_label.setText("✓ You have already completed all positions in this election.")
            self.warning_label.setStyleSheet("color: #10B981; font-weight: bold;")
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setText("⚠ Please select a candidate (or Abstain) for each remaining position before submitting.")
            self.warning_label.setStyleSheet("color: #F59E0B;")
            self.warning_label.setVisible(not all_remaining_completed)

    def _on_submit(self):
        votes = []
        for section in self._position_sections:
            if section.is_locked():
                continue
            candidate_id = section.get_selected_candidate_id()
            if candidate_id is not None:
                votes.append({
                    "position_id": section.position_id,
                    "candidate_id": None if int(candidate_id) == 0 else candidate_id
                })
        if votes:
            self.ballot_submitted.emit(votes)
            self.accept()

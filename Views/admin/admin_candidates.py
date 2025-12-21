"""
Manage Candidates Page - CRUD operations for candidates
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QScrollArea, QDialog, QLineEdit,
    QComboBox, QMessageBox, QPushButton, QFileDialog, QPlainTextEdit
)
from PyQt6.QtGui import QFont, QColor, QCursor, QPixmap
from PyQt6.QtCore import Qt

from .admin_components import GreenButton, ActionButton
from Views.components import CircularImageAvatar
from Controller.controller_candidates import (
    list_candidates,
    list_elections_options,
    create_candidate,
    update_candidate,
    delete_candidate,
    list_candidate_users,
)


class CandidateDialog(QDialog):
    """Dialog for creating/editing a candidate"""

    def __init__(self, parent=None, candidate: dict = None, elections: list = None):
        super().__init__(parent)
        self.candidate = candidate
        self.elections = elections or []
        self.photo_path = candidate.get('photo_path', '') if candidate else ''
        self.users = list_candidate_users()
        self.selected_user = None

        self.setWindowTitle("Edit Candidate" if candidate else "Add Candidate")
        self.setMinimumSize(560, 660)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 36)
        layout.setSpacing(14)

        title = QLabel("Edit Candidate" if candidate else "Add New Candidate")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(10)

        # Scrollable form container so buttons don't overlap
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(16)

        form_style = """
            QLineEdit, QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #111827;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4B5563;
                background-color: #FFFFFF;
            }
        """

        # Make sure combo box popup is white and items don't show green tint
        form_style += """
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                color: #111827;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                background: transparent;
                color: #111827;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #E5E7EB;
                color: #111827;
            }
        """

        label_style = """
            color: #374151;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            margin-bottom: 8px;
        """

        # User selector (candidates are users)
        user_label = QLabel("Select User")
        user_label.setStyleSheet(label_style)
        form_layout.addWidget(user_label)

        self.user_combo = QComboBox()
        self.user_combo.setStyleSheet(form_style + "QComboBox { padding-top: 8px; padding-bottom: 8px; }")
        self.user_combo.setFixedHeight(48)
        self.user_combo.addItem("Select user", None)
        for u in self.users:
            display = f"{u.get('full_name')} ({u.get('student_id') or 'no ID'})"
            self.user_combo.addItem(display, u.get('user_id'))
        try:
            self.user_combo.view().setMinimumWidth(320)
        except Exception:
            pass
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        form_layout.addWidget(self.user_combo)

        # Name (read-only, mirrors selected user)
        name_label = QLabel("Full Name")
        name_label.setStyleSheet(label_style)
        form_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Select a user")
        self.name_input.setReadOnly(True)
        self.name_input.setStyleSheet(form_style)
        self.name_input.setFixedHeight(46)
        form_layout.addWidget(self.name_input)

        # Position
        position_label = QLabel("Position")
        position_label.setStyleSheet(label_style)
        form_layout.addWidget(position_label)

        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("e.g., President, Vice President")
        self.position_input.setStyleSheet(form_style)
        self.position_input.setFixedHeight(46)
        form_layout.addWidget(self.position_input)

        # Slogan
        slogan_label = QLabel("Campaign Slogan")
        slogan_label.setStyleSheet(label_style)
        form_layout.addWidget(slogan_label)

        self.slogan_input = QLineEdit()
        self.slogan_input.setPlaceholderText("Enter campaign slogan")
        self.slogan_input.setStyleSheet(form_style)
        self.slogan_input.setFixedHeight(46)
        form_layout.addWidget(self.slogan_input)

        # Bio
        bio_label = QLabel("Bio")
        bio_label.setStyleSheet(label_style)
        form_layout.addWidget(bio_label)

        self.bio_input = QLineEdit()
        self.bio_input.setPlaceholderText("Short bio/background")
        self.bio_input.setStyleSheet(form_style)
        self.bio_input.setFixedHeight(46)
        form_layout.addWidget(self.bio_input)

        # Email
        email_label = QLabel("Email")
        email_label.setStyleSheet(label_style)
        form_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("candidate@example.com")
        self.email_input.setStyleSheet(form_style)
        self.email_input.setFixedHeight(46)
        form_layout.addWidget(self.email_input)

        # Phone
        phone_label = QLabel("Phone")
        phone_label.setStyleSheet(label_style)
        form_layout.addWidget(phone_label)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(555) 123-4567")
        self.phone_input.setStyleSheet(form_style)
        self.phone_input.setFixedHeight(46)
        form_layout.addWidget(self.phone_input)

        # Platform
        platform_label = QLabel("Platform")
        platform_label.setStyleSheet(label_style)
        form_layout.addWidget(platform_label)

        self.platform_input = QPlainTextEdit()
        self.platform_input.setPlaceholderText("Enter bullet points; separate with '|' or new lines")
        self.platform_input.setStyleSheet(form_style + "QPlainTextEdit { min-height: 140px; color: #111827; }")
        self.platform_input.setFixedHeight(150)
        form_layout.addWidget(self.platform_input)

        # Elections dropdown (filtered)
        election_label = QLabel("Election")
        election_label.setStyleSheet(label_style)
        form_layout.addWidget(election_label)

        self.election_combo = QComboBox()
        self.election_combo.setStyleSheet(form_style)
        self.election_combo.setFixedHeight(48)
        self.election_combo.addItem("Select election", None)
        for e in self.elections:
            self.election_combo.addItem(e.get('title', 'Election'), e.get('election_id'))
        form_layout.addWidget(self.election_combo)

        # Photo
        photo_label_title = QLabel("Candidate Photo")
        photo_label_title.setStyleSheet(label_style)
        form_layout.addWidget(photo_label_title)

        photo_container = QFrame()
        photo_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px dashed #D1D5DB;
                border-radius: 10px;
            }
        """)
        photo_container.setFixedHeight(72)
        photo_layout = QHBoxLayout(photo_container)
        photo_layout.setContentsMargins(16, 12, 16, 12)

        self.photo_label = QLabel("No photo selected")
        self.photo_label.setStyleSheet("color: #9CA3AF; font-size: 13px; background: transparent; margin-right: 8px;")

        photo_btn = QPushButton("Choose Photo")
        photo_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        photo_btn.setFont(QFont("Segoe UI", 12))
        photo_btn.setFixedHeight(40)
        photo_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
            }
            QPushButton:hover { background: #059669; }
        """)
        photo_btn.clicked.connect(self._choose_photo)

        photo_layout.addWidget(self.photo_label, 1)
        photo_layout.addWidget(photo_btn)
        form_layout.addWidget(photo_container)

        form_layout.addStretch()

        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        # Pre-fill if editing
        if candidate:
            # Try to select matching user
            uid = candidate.get('user_id')
            if uid:
                idx = self.user_combo.findData(uid)
                if idx != -1:
                    self.user_combo.setCurrentIndex(idx)
            self.name_input.setText(candidate.get('full_name', ''))
            self.position_input.setText(candidate.get('position', 'President'))
            self.slogan_input.setText(candidate.get('slogan', ''))
            self.bio_input.setText(candidate.get('bio', '') or '')
            self.email_input.setText(candidate.get('email', '') or '')
            self.phone_input.setText(candidate.get('phone', '') or '')
            self.platform_input.setPlainText(candidate.get('platform', '') or '')
            if candidate.get('election_id'):
                idx = self.election_combo.findData(candidate.get('election_id'))
                if idx != -1:
                    self.election_combo.setCurrentIndex(idx)
            if self.photo_path:
                self.photo_label.setText(os.path.basename(self.photo_path))

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFont(QFont("Segoe UI", 13))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F3F4F6;
                border: 2px solid #E5E7EB;
                border-radius: 25px;
                padding: 12px 35px;
                color: #6B7280;
                font-weight: 600;
            }
            QPushButton:hover { 
                background: #E5E7EB;
                color: #374151;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Candidate")
        save_btn.setFixedHeight(50)
        save_btn.setMinimumWidth(160)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 35px;
            }
            QPushButton:hover { 
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _choose_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.photo_path = file_path
            self.photo_label.setText(os.path.basename(file_path))

    def get_data(self) -> dict:
        selected_election = self.election_combo.currentData()
        selected_elections = [selected_election] if selected_election else []
        return {
            'full_name': self.name_input.text().strip(),
            'position': self.position_input.text().strip() or 'President',
            'slogan': self.slogan_input.text().strip(),
            'bio': self.bio_input.text().strip(),
            'email': self.email_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'platform': self.platform_input.toPlainText().strip(),
            'election_ids': selected_elections,
            'photo_path': self.photo_path,
            'user_id': self.user_combo.currentData(),
        }

    def _on_user_changed(self, index: int):
        uid = self.user_combo.currentData()
        if uid:
            match = next((u for u in self.users if u.get('user_id') == uid), None)
            if match:
                self.name_input.setText(match.get('full_name', ''))
        else:
            self.name_input.clear()

    def accept(self):
        email = (self.email_input.text() or "").strip()
        if email and "@" not in email:
            QMessageBox.warning(self, "Invalid Email", "Email must contain '@'.")
            return
        super().accept()


class CandidateCard(QFrame):
    """Card displaying a candidate with edit/delete actions"""

    def __init__(self, candidate: dict, on_edit=None, on_delete=None):
        super().__init__()
        self.candidate = candidate
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.setFixedSize(320, 320)
        self.setStyleSheet("""
            CandidateCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 25)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Avatar
        photo = candidate.get('photo_path')
        if photo and not os.path.isabs(photo):
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            photo = os.path.join(base, photo)

        avatar = CircularImageAvatar(photo, candidate.get('full_name', '?')[0], size=100)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name
        name_lbl = QLabel(candidate.get('full_name', 'Unknown'))
        name_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #111827;")
        layout.addWidget(name_lbl)

        # Position
        position_lbl = QLabel(candidate.get('position', 'President'))
        position_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        position_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        position_lbl.setStyleSheet("color: #10B981;")
        layout.addWidget(position_lbl)

        # Slogan
        slogan_lbl = QLabel(candidate.get('slogan', ''))
        slogan_lbl.setFont(QFont("Segoe UI", 10))
        slogan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_lbl.setStyleSheet("color: #9CA3AF; font-style: italic;")
        slogan_lbl.setWordWrap(True)
        slogan_lbl.setMaximumHeight(40)
        layout.addWidget(slogan_lbl)

        layout.addStretch()

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        edit_btn = ActionButton("edit", "Edit")
        delete_btn = ActionButton("delete", "Delete")

        edit_btn.clicked.connect(lambda: self.on_edit(candidate) if self.on_edit else None)
        delete_btn.clicked.connect(lambda: self.on_delete(candidate) if self.on_delete else None)

        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)


class ManageCandidatesPage(QWidget):
    """Page for managing candidates"""

    def __init__(self):
        super().__init__()
        self._candidates = []
        self._elections = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main card
        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 35, 40, 35)
        card_layout.setSpacing(25)

        # Header row
        header_row = QHBoxLayout()

        title = QLabel("All Candidates")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")

        add_btn = GreenButton("Add Candidate")
        add_btn.clicked.connect(self._add_candidate)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(add_btn)
        card_layout.addLayout(header_row)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(25)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        scroll.setWidget(self.grid_widget)
        card_layout.addWidget(scroll, 1)

        layout.addWidget(card)

    def _load_data(self):
        """Load candidates and elections from database"""
        try:
            self._elections = list_elections_options()
            self._candidates = list_candidates()
            self._populate_grid()
        except Exception as e:
            print(f"Load candidates error: {e}")

    def _populate_grid(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add cards
        row, col = 0, 0
        max_cols = 3
        for candidate in self._candidates:
            card = CandidateCard(
                candidate,
                on_edit=self._edit_candidate,
                on_delete=self._delete_candidate
            )
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _add_candidate(self):
        dialog = CandidateDialog(self, elections=self._elections)
        if dialog.exec():
            data = dialog.get_data()
            if not data['full_name']:
                QMessageBox.warning(self, "Error", "Name is required")
                return
            if not data['election_ids']:
                QMessageBox.warning(self, "Error", "Select at least one election")
                return

            ok, msg = create_candidate(data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def _edit_candidate(self, candidate: dict):
        dialog = CandidateDialog(self, candidate=candidate, elections=self._elections)
        if dialog.exec():
            data = dialog.get_data()
            if not data['election_ids']:
                QMessageBox.warning(self, "Error", "Select at least one election")
                return
            ok, msg = update_candidate(candidate['candidate_id'], data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def _delete_candidate(self, candidate: dict):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {candidate.get('full_name')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = delete_candidate(candidate['candidate_id'])
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def refresh(self):
        self._load_data()

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton,
    QStackedWidget, QStyle, QGraphicsDropShadowEffect, QMessageBox, QMenu,
    QDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QCursor, QPixmap
import os

from Views.components import SidebarButton, CircularAvatar, CircularImageAvatar
from Views.views_dashboard import DashboardPage
from Views.views_history import HistoryPage
from Views.views_candidate import CandidatesPage
from Views.views_results import ResultsPage
from Controller.controller_voters import (
    get_user_by_id, update_user_profile, get_user_voting_history,
    has_user_voted, cast_vote
)
from Controller.controller_elections import get_election_results
from Controller.controller_candidates import get_candidates_for_election
from Models.model_db import Database


class MainWindow(QMainWindow):
    def __init__(self, user_data: dict = None, on_logout=None):
        """
        user_data: dict with keys id, name, role (from login)
        on_logout: optional callback to return to login screen
        """
        super().__init__()
        self.user_data = user_data or {"id": None, "name": "Student Name", "role": "student"}
        self.on_logout = on_logout

        self.resize(1300, 800)
        self.setWindowTitle("EduVote")

        container = QWidget()
        container.setStyleSheet("background-color: #ECFDF5;")
        self.setCentralWidget(container)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Sidebar ──────────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #FFFFFF;")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(15, 25, 15, 25)
        sb_layout.setSpacing(8)

        # Logo / brand
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 20)

        logo_img = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "logo-generator (1).jpg")
        logo_pm = QPixmap(logo_path)
        if not logo_pm.isNull():
            logo_pm = logo_pm.scaled(150, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_img.setPixmap(logo_pm)
            logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            # Fallback to text if logo is missing
            logo_img.setText("EduVote")
            logo_img.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            logo_img.setStyleSheet("color: #10B981;")
            logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_layout.addWidget(logo_img, alignment=Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(logo_container)

        # Nav buttons with icons matching mockup
        self.btn_vote = SidebarButton("Vote Now", "✓")  # checkmark
        self.btn_history = SidebarButton("My History", "⟳")  # circular arrow
        self.btn_candidates = SidebarButton("Candidates", "👥")  # people icon
        self.btn_results = SidebarButton("Results", "📈")  # chart increasing

        self.btn_vote.clicked.connect(lambda: self.switch_page(0))
        self.btn_history.clicked.connect(lambda: self.switch_page(1))
        self.btn_candidates.clicked.connect(lambda: self.switch_page(2))
        self.btn_results.clicked.connect(lambda: self.switch_page(3))

        sb_layout.addWidget(self.btn_vote)
        sb_layout.addWidget(self.btn_history)
        sb_layout.addWidget(self.btn_candidates)
        sb_layout.addWidget(self.btn_results)
        sb_layout.addStretch()

        # ─── Right content area ───────────────────────────────────────
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(30, 20, 30, 20)
        right_layout.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()
        display_name = self.user_data.get('name') or self.user_data.get('full_name') or 'Student Name'
        greeting = QLabel(f"Hello, <b>{display_name}</b>")
        greeting.setTextFormat(Qt.TextFormat.RichText)
        greeting.setFont(QFont("Segoe UI", 16))
        greeting.setStyleSheet("color: #111827;")
        self._greeting_label = greeting

        online_dot = QLabel("●")
        online_dot.setStyleSheet("color: #10B981; font-size: 10px;")

        profile_btn = QPushButton()
        profile_btn.setFixedSize(45, 45)
        profile_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        profile_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1F2937;
                border-radius: 22px;
                color: white;
                font-size: 18px;
            }
            QPushButton:hover { background-color: #374151; }
            """
        )
        profile_btn.setText("👤")

        # Profile menu with logout
        self.profile_menu = QMenu(self)
        edit_action = self.profile_menu.addAction("Edit Profile")
        edit_action.triggered.connect(self._open_profile_dialog)
        logout_action = self.profile_menu.addAction("Log out")
        logout_action.triggered.connect(self._handle_logout)
        profile_btn.clicked.connect(lambda: self.profile_menu.exec(profile_btn.mapToGlobal(profile_btn.rect().bottomLeft())))

        top_bar.addWidget(greeting)
        top_bar.addWidget(online_dot)
        top_bar.addStretch()
        top_bar.addWidget(profile_btn)

        right_layout.addLayout(top_bar)
        right_layout.addSpacing(15)

        # Page stack
        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(self.user_data)
        self.history_page = HistoryPage()
        self.candidates_page = CandidatesPage()
        self.results_page = ResultsPage(self.user_data)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.candidates_page)
        self.stack.addWidget(self.results_page)

        right_layout.addWidget(self.stack)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(right_area, 1)

        # Load election data and wire vote handler
        self._load_election_data()
        self._load_history_data()
        self.dashboard_page.set_vote_handler(self._handle_vote)

        self.switch_page(0)

    def _handle_logout(self):
        if callable(self.on_logout):
            self.on_logout()
        else:
            self.close()

    # ─── Profile Editing ───────────────────────────────────────────
    def _open_profile_dialog(self):
        user_id = self.user_data.get("id") or self.user_data.get("user_id")
        if not user_id:
            QMessageBox.warning(self, "Not Logged In", "No user loaded.")
            return

        user = get_user_by_id(user_id)
        if not user:
            QMessageBox.warning(self, "Error", "Could not load your profile.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Profile")
        dialog.setModal(True)
        dialog.setFixedSize(420, 320)

        form = QFormLayout(dialog)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        name_edit = QLineEdit(user.get("full_name", ""))
        email_edit = QLineEdit(user.get("email", ""))
        sid_edit = QLineEdit(user.get("student_id", ""))
        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_edit.setPlaceholderText("Leave blank to keep current password")

        for w in (name_edit, email_edit, sid_edit, pwd_edit):
            w.setMinimumHeight(32)
            w.setStyleSheet("border:1px solid #D1D5DB; border-radius:8px; padding:6px 8px;")

        form.addRow("Full name", name_edit)
        form.addRow("Email", email_edit)
        form.addRow("Student ID", sid_edit)
        form.addRow("New password", pwd_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("background:#10B981; color:white; border:none; border-radius:10px; padding:8px 16px;")
        btn_row.addWidget(save_btn)
        form.addRow(btn_row)

        def save():
            new_pwd = pwd_edit.text().strip()

            email_val = (email_edit.text() or "").strip()
            if email_val and "@" not in email_val:
                QMessageBox.warning(self, "Invalid Email", "Email must contain '@'.")
                return

            success, msg = update_user_profile(
                user_id,
                name_edit.text(),
                email_edit.text(),
                sid_edit.text(),
                new_pwd if new_pwd else None,
            )
            if success:
                self.user_data["name"] = name_edit.text()
                self.user_data["email"] = email_edit.text()
                self.user_data["student_id"] = sid_edit.text()
                QMessageBox.information(self, "Profile updated", msg)
                dialog.accept()
                self._refresh_greeting()
            else:
                QMessageBox.warning(self, "Update failed", msg)

        save_btn.clicked.connect(save)
        dialog.exec()

    def _refresh_greeting(self):
        if hasattr(self, "_greeting_label"):
            display_name = self.user_data.get('name') or self.user_data.get('full_name') or 'Student Name'
            self._greeting_label.setText(f"Hello, <b>{display_name}</b>")

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_vote.set_active(index == 0)
        self.btn_history.set_active(index == 1)
        self.btn_candidates.set_active(index == 2)
        self.btn_results.set_active(index == 3)

    def _load_election_data(self):
        user_id = self.user_data.get("id") or self.user_data.get("user_id")
        db = Database()
        elections = db.get_user_allowed_elections(user_id) if user_id else []

        blocks = []
        for e in elections:
            end_date = e.get("end_date")
            end_date_fmt = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else (str(end_date) if end_date else "TBD")
            start_date = e.get("start_date")
            start_date_fmt = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else (str(start_date) if start_date else "TBD")
            candidates = get_candidates_for_election(e.get("election_id"))
            user_voted = has_user_voted(user_id, e.get("election_id")) if user_id else False
            blocks.append({
                "election": {
                    "election_id": e.get("election_id"),
                    "title": e.get("title", "Election"),
                    "status": e.get("status", "upcoming"),
                    "start_date": start_date_fmt,
                    "end_date": end_date_fmt,
                    "user_voted": user_voted,
                },
                "candidates": candidates
            })

        self.dashboard_page.set_elections(blocks)

    def _load_history_data(self):
        user_id = self.user_data.get("id") or self.user_data.get("user_id")
        rows = get_user_voting_history(user_id) if user_id else []
        if hasattr(self, "history_page"):
            self.history_page.set_history(rows)

    def _handle_vote(self, election_id: int, candidate_id: int):
        user_id = self.user_data.get("id") or self.user_data.get("user_id")
        if not user_id:
            QMessageBox.warning(self, "Not Logged In", "You must be logged in to vote.")
            return

        if not election_id:
            QMessageBox.warning(self, "No Election", "No active election found.")
            return

        success, message = cast_vote(user_id, election_id, candidate_id)
        if success:
            candidates = get_candidates_for_election(election_id) or []
            candidate_name = next((c.get("full_name") for c in candidates if c.get("candidate_id") == candidate_id), "your candidate")
            QMessageBox.information(self, "Vote Submitted", f"You voted for {candidate_name}!\n\n{message}")
            self._load_election_data()
            self._load_history_data()
            self.results_page.refresh()
        else:
            msg = message or "Vote failed."
            if "already voted" in str(msg).lower():
                QMessageBox.information(self, "Already Voted", msg)
            else:
                QMessageBox.warning(self, "Vote Failed", msg)
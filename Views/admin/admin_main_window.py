"""
Admin Main Window - Main container for admin panel with sidebar navigation
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QGraphicsDropShadowEffect, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QCursor, QPixmap
import os

from .admin_components import AdminSidebarButton
from .admin_dashboard import AdminDashboardPage
from .admin_elections import ManageElectionsPage
from .admin_candidates import ManageCandidatesPage
from .admin_results import AdminResultsPage
from .admin_voters import ManageVotersPage


class AdminMainWindow(QMainWindow):
    """Main window for the admin panel"""

    def __init__(self, user_data: dict = None, on_logout=None):
        super().__init__()
        self.user_data = user_data or {"id": None, "name": "Admin", "role": "admin"}
        self.on_logout = on_logout

        self.setWindowTitle("EduVote - Admin Panel")
        self.resize(1400, 850)

        self._setup_ui()
        self._switch_page(0)

    def _setup_ui(self):
        container = QWidget()
        container.setStyleSheet("background-color: #ECFDF5;")
        self.setCentralWidget(container)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Sidebar ──────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #FFFFFF;")

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(18, 25, 18, 25)
        sb_layout.setSpacing(6)

        # Logo
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 25)

        logo_img = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "logo-generator (1).jpg")
        logo_pm = QPixmap(logo_path)
        if not logo_pm.isNull():
            logo_pm = logo_pm.scaled(160, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_img.setPixmap(logo_pm)
            logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            logo_img.setText("EduVote")
            logo_img.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            logo_img.setStyleSheet("color: #10B981;")
            logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_layout.addWidget(logo_img, alignment=Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(logo_container)

        # Navigation buttons
        self.btn_dashboard = AdminSidebarButton("Dashboard", "⊞")
        self.btn_elections = AdminSidebarButton("Manage Elections", "☑")
        self.btn_candidates = AdminSidebarButton("Candidates", "👥")
        self.btn_results = AdminSidebarButton("View Results", "📈")
        self.btn_voters = AdminSidebarButton("Voters", "👤")

        self.btn_dashboard.clicked.connect(lambda: self._switch_page(0))
        self.btn_elections.clicked.connect(lambda: self._switch_page(1))
        self.btn_candidates.clicked.connect(lambda: self._switch_page(2))
        self.btn_results.clicked.connect(lambda: self._switch_page(3))
        self.btn_voters.clicked.connect(lambda: self._switch_page(4))

        sb_layout.addWidget(self.btn_dashboard)
        sb_layout.addWidget(self.btn_elections)
        sb_layout.addWidget(self.btn_candidates)
        sb_layout.addWidget(self.btn_results)
        sb_layout.addWidget(self.btn_voters)
        sb_layout.addStretch()

        # ─── Right content area ───────────────────────────────────────
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(30, 20, 30, 20)
        right_layout.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()

        self.page_title = QLabel("Admin Panel")
        self.page_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color: #111827;")

        profile_btn = QPushButton()
        profile_btn.setFixedSize(48, 48)
        profile_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border-radius: 24px;
                color: white;
                font-size: 20px;
            }
            QPushButton:hover { background-color: #374151; }
        """)
        profile_btn.setText("👤")

        # Profile menu with logout
        self.profile_menu = QMenu(self)
        self.profile_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px;
                color: #111827;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 4px;
                color: #111827;
            }
            QMenu::item:selected {
                background-color: #E5F3FF;
                color: #0F172A;
            }
        """)
        logout_action = self.profile_menu.addAction("🚪  Log out")
        logout_action.triggered.connect(self._handle_logout)
        profile_btn.clicked.connect(
            lambda: self.profile_menu.exec(profile_btn.mapToGlobal(profile_btn.rect().bottomLeft()))
        )

        top_bar.addWidget(self.page_title)
        top_bar.addStretch()
        top_bar.addWidget(profile_btn)

        right_layout.addLayout(top_bar)
        right_layout.addSpacing(20)

        # Page stack
        self.stack = QStackedWidget()

        self.dashboard_page = AdminDashboardPage()
        self.elections_page = ManageElectionsPage()
        self.candidates_page = ManageCandidatesPage()
        self.results_page = AdminResultsPage()
        self.voters_page = ManageVotersPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.elections_page)
        self.stack.addWidget(self.candidates_page)
        self.stack.addWidget(self.results_page)
        self.stack.addWidget(self.voters_page)

        right_layout.addWidget(self.stack)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(right_area, 1)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)

        # Update active states
        self.btn_dashboard.set_active(index == 0)
        self.btn_elections.set_active(index == 1)
        self.btn_candidates.set_active(index == 2)
        self.btn_results.set_active(index == 3)
        self.btn_voters.set_active(index == 4)

        # Update page title
        titles = ["Admin Panel", "Manage Elections", "Manage Candidates", "Election Results", "Manage Voters"]
        self.page_title.setText(titles[index])

        # Refresh the page data
        current_page = self.stack.currentWidget()
        if hasattr(current_page, 'refresh'):
            current_page.refresh()

    def _handle_logout(self):
        confirm = QMessageBox.question(
            self,
            "Confirm Log out",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        if callable(self.on_logout):
            self.on_logout()
        else:
            self.close()

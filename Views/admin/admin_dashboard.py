
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QDialog
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer

from .admin_components import StatCard, BarChart
from Controller.controller_elections import (
    get_admin_stats,
    get_dashboard_chart_data,
)
from Controller.controller_audit_log import get_recent_activity


class ActivityItem(QFrame):
    """Single activity item in the recent activity list"""

    def __init__(self, text: str, time_ago: str, date_text: str | None = None):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Avatar
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: transparent;
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            font-size: 16px;
            color: #10B981;
        """)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        msg = QLabel(text)
        msg.setFont(QFont("Segoe UI", 11))
        msg.setStyleSheet("color: #111827;")
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        msg.setMinimumWidth(0)

        time_lbl = QLabel(date_text or time_ago)
        time_lbl.setFont(QFont("Segoe UI", 9))
        time_lbl.setStyleSheet("color: #9CA3AF;")
        time_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        text_layout.addWidget(msg)
        text_layout.addWidget(time_lbl)

        layout.addWidget(avatar)
        layout.addLayout(text_layout, 1)


class RecentActivityPanel(QFrame):
    """Panel showing recent voting activity"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            RecentActivityPanel {
                background-color: transparent;
                border-radius: 16px;
            }
        """)
        self.setMinimumWidth(300)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("Audit Logs:")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        title_row.addWidget(title)
        title_row.addStretch(1)

        self.view_all_btn = QPushButton("View All")
        self.view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_all_btn.setFixedHeight(30)
        self.view_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #10B981;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ECFDF5;
            }
        """)
        title_row.addWidget(self.view_all_btn)
        layout.addLayout(title_row)
        # Scrollable activity list to keep panel compact
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.activity_scroll.setStyleSheet("background: transparent;")
        self.activity_scroll.setFixedHeight(320)

        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(8)
        self.activity_layout.addStretch(1)

        self.activity_scroll.setWidget(self.activity_container)
        layout.addWidget(self.activity_scroll)

    def add_activity(self, text: str, time_ago: str, date_text: str | None = None):
        item = ActivityItem(text, time_ago, date_text=date_text)
        # Insert before the stretch
        self.activity_layout.insertWidget(max(0, self.activity_layout.count() - 1), item)

    def clear_activities(self):
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # Restore stretch at bottom
        self.activity_layout.addStretch(1)

    def set_view_all_handler(self, handler):
        self.view_all_btn.clicked.connect(handler)


class AdminDashboardPage(QWidget):
    """Main admin dashboard page"""

    def __init__(self):
        super().__init__()
        self._chart_mode = "results"
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)

        self.total_voters_card = StatCard("Total Voters:", "0", "👥", dark=True)
        self.votes_casted_card = StatCard("Vote Casted:", "0", "☑", dark=True)
        self.participation_card = StatCard("Participation Rate:", "0 %", "📈", dark=True)
        self.active_elections_card = StatCard("Active Elections:", "0", "☑", dark=True)

        stats_row.addWidget(self.total_voters_card)
        stats_row.addWidget(self.votes_casted_card)
        stats_row.addWidget(self.participation_card)
        stats_row.addWidget(self.active_elections_card)

        layout.addLayout(stats_row)

        # Main content row (chart + activity)
        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # Chart card
        chart_card = QFrame()
        chart_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        chart_card.setGraphicsEffect(shadow)

        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(30, 25, 30, 25)

        self.chart_title = QLabel("Live Election Results")
        self.chart_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.chart_title.setStyleSheet("color: #111827;")
        chart_layout.addWidget(self.chart_title)

        # Chart mode selector
        mode_row = QHBoxLayout()
        mode_row.addStretch(1)

        # No dropdowns here (keeps dashboard clean). Always show live results by position.
        chart_layout.addLayout(mode_row)

        self.bar_chart = BarChart()
        self.bar_chart.setMinimumHeight(260)
        chart_layout.addWidget(self.bar_chart, 1)

        content_row.addWidget(chart_card, 2)

        # Recent activity
        self.activity_panel = RecentActivityPanel()
        self.activity_panel.set_view_all_handler(self._open_audit_log_dialog)
        content_row.addWidget(self.activity_panel, 1)

        layout.addLayout(content_row, 1)

    def _load_data(self):
        """Load dashboard data using controllers"""
        try:
            # Get admin stats from controller
            stats = get_admin_stats()
            self.total_voters_card.set_value(str(stats['total_voters']))
            self.votes_casted_card.set_value(str(stats['votes_cast']))
            self.participation_card.set_value(f"{stats['participation_rate']:.0f} %")
            self.active_elections_card.set_value(str(stats['active_elections']))

            # Get chart data from controller
            self._load_chart()

            # Get audit activity from controller
            self.activity_panel.clear_activities()
            activities = get_recent_activity(8)
            if not activities:
                self.activity_panel.add_activity("System: No audit logs yet.", "", date_text="")

            for row in activities:
                created_at = row.get('created_at')
                try:
                    date_text = created_at.strftime('%Y-%m-%d %H:%M') if hasattr(created_at, 'strftime') else str(created_at or '')
                except Exception:
                    date_text = str(created_at or '')

                user_name = row.get("user_name") or "System"
                action = row.get("action") or "Activity"
                details = row.get("details") or ""
                message = f"{user_name}: {action}" if not details else f"{user_name}: {action} — {details}"

                self.activity_panel.add_activity(message, "recently", date_text=date_text)

        except Exception as e:
            print(f"Dashboard load error: {e}")
            # Show placeholder data
            self.activity_panel.add_activity("System: Audit logs are unavailable.", "", date_text="")

            self.bar_chart.set_data([
                ("Item 1", 7), ("Item 2", 11), ("Item 3", 15),
                ("Item 4", 18), ("Item 5", 20), ("Item 6", 22)
            ])

    def _open_audit_log_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("All Audit Logs")
        dialog.setMinimumSize(680, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("All Audit Logs")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        loading = QLabel("Loading audit logs...")
        loading.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(loading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        def _load_logs():
            logs = get_recent_activity(None)
            loading.setVisible(False)

            if not logs:
                empty = QLabel("No audit logs found.")
                empty.setStyleSheet("color: #6B7280; font-size: 12px;")
                content_layout.addWidget(empty)
            else:
                for row in logs:
                    created_at = row.get("created_at")
                    try:
                        date_text = created_at.strftime('%Y-%m-%d %H:%M') if hasattr(created_at, 'strftime') else str(created_at or '')
                    except Exception:
                        date_text = str(created_at or '')

                    user_name = row.get("user_name") or "System"
                    action = row.get("action") or "Activity"
                    details = row.get("details") or ""
                    message = f"{user_name}: {action}" if not details else f"{user_name}: {action} — {details}"

                    content_layout.addWidget(ActivityItem(message, "", date_text=date_text))

            content_layout.addStretch(1)

        QTimer.singleShot(50, _load_logs)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 6px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    def _load_chart(self):
        chart_info = get_dashboard_chart_data("results")
        self.chart_title.setText(chart_info.get('title', 'Dashboard'))
        self.bar_chart.set_data(chart_info.get('data', []))

    def refresh(self):
        """Refresh dashboard data"""
        self._load_data()

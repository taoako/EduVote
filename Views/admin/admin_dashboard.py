"""
Admin Dashboard Page - Main overview with stats, charts, and recent activity
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from .admin_components import StatCard, BarChart
from Models.model_db import Database


class ActivityItem(QFrame):
    """Single activity item in the recent activity list"""

    def __init__(self, text: str, time_ago: str):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Avatar
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #D1FAE5;
            border-radius: 18px;
            font-size: 16px;
        """)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        msg = QLabel(text)
        msg.setFont(QFont("Segoe UI", 11))
        msg.setStyleSheet("color: #111827;")
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        time_lbl = QLabel(time_ago)
        time_lbl.setFont(QFont("Segoe UI", 9))
        time_lbl.setStyleSheet("color: #9CA3AF;")

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
                background-color: #FFFFFF;
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

        title = QLabel("Recent Activity:")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        self.activity_layout = QVBoxLayout()
        self.activity_layout.setSpacing(8)
        layout.addLayout(self.activity_layout)
        layout.addStretch()

    def add_activity(self, text: str, time_ago: str):
        item = ActivityItem(text, time_ago)
        self.activity_layout.addWidget(item)

    def clear_activities(self):
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class AdminDashboardPage(QWidget):
    """Main admin dashboard page"""

    def __init__(self):
        super().__init__()
        self.db = Database()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

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

        self.bar_chart = BarChart()
        chart_layout.addWidget(self.bar_chart, 1)

        content_row.addWidget(chart_card, 2)

        # Recent activity
        self.activity_panel = RecentActivityPanel()
        content_row.addWidget(self.activity_panel, 1)

        layout.addLayout(content_row, 1)

    def _load_data(self):
        """Load dashboard data from database"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return

            cursor = conn.cursor(dictionary=True)

            # Total voters
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
            total_voters = cursor.fetchone()['count']
            self.total_voters_card.set_value(str(total_voters))

            # Votes casted (total voting records)
            cursor.execute("SELECT COUNT(*) as count FROM voting_records")
            votes_casted = cursor.fetchone()['count']
            self.votes_casted_card.set_value(str(votes_casted))

            # Participation rate
            if total_voters > 0:
                rate = (votes_casted / total_voters) * 100
                self.participation_card.set_value(f"{rate:.0f} %")

            # Active elections
            cursor.execute("SELECT COUNT(*) as count FROM elections WHERE status = 'active'")
            active_count = cursor.fetchone()['count']
            self.active_elections_card.set_value(str(active_count))

            # Chart data - prefer latest active; fallback to most recent election with candidates
            chart_data = []
            title_text = "Live Election Results"

            cursor.execute(
                """
                SELECT * FROM elections
                WHERE status = 'active'
                ORDER BY start_date DESC, election_id DESC
                LIMIT 1
                """
            )
            active = cursor.fetchone()

            target_election = active
            if not target_election:
                cursor.execute(
                    """
                    SELECT e.*
                    FROM elections e
                    WHERE EXISTS (
                        SELECT 1 FROM candidates c WHERE c.election_id = e.election_id
                    )
                    ORDER BY COALESCE(e.end_date, e.start_date) DESC, e.election_id DESC
                    LIMIT 1
                    """
                )
                target_election = cursor.fetchone()

            if target_election:
                # Aggregate votes from voting_records to avoid stale vote_count
                cursor.execute(
                    """
                    SELECT c.full_name,
                           COALESCE(v.vote_total, c.vote_count, 0) AS votes
                    FROM candidates c
                    LEFT JOIN (
                        SELECT candidate_id, COUNT(*) AS vote_total
                        FROM voting_records
                        WHERE candidate_id IS NOT NULL
                        GROUP BY candidate_id
                    ) v ON v.candidate_id = c.candidate_id
                    WHERE c.election_id = %s
                    ORDER BY votes DESC
                    """,
                    (target_election['election_id'],),
                )
                chart_data = [(row['full_name'], row['votes']) for row in cursor.fetchall()]
                title_text = f"Live Election Results: {target_election.get('title', 'Election')}"

            self.chart_title.setText(title_text)
            self.bar_chart.set_data(chart_data)

            # Recent activity (mock data for now - would need voting_records with timestamps)
            self.activity_panel.clear_activities()
            cursor.execute("""
                SELECT u.full_name, e.title AS election_title, vr.voted_at
                FROM voting_records vr
                JOIN users u ON vr.user_id = u.user_id
                JOIN elections e ON vr.election_id = e.election_id
                ORDER BY vr.voted_at DESC LIMIT 5
            """)
            for row in cursor.fetchall():
                self.activity_panel.add_activity(
                    f"{row['full_name']}: voted in {row['election_title']}",
                    "recently"
                )

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Dashboard load error: {e}")
            # Show placeholder data
            self.activity_panel.add_activity("Student: Voted Mang Kanor", "2 hours ago")
            self.activity_panel.add_activity("Student: Voted Mang Kanor", "2 hours ago")
            self.activity_panel.add_activity("Student: Voted Mang Kanor", "2 hours ago")

            self.bar_chart.set_data([
                ("Item 1", 7), ("Item 2", 11), ("Item 3", 15),
                ("Item 4", 18), ("Item 5", 20), ("Item 6", 22)
            ])

    def refresh(self):
        """Refresh dashboard data"""
        self._load_data()

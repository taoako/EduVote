from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QTableWidgetItem, QProgressBar, QScrollArea, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QMenu
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt
from datetime import datetime
import os

# Update these imports to match your project structure
from .admin_components import StatusBadge, DataTable, BarChart, PieChart, WinnerBanner
from Models.model_db import Database
from Controller.controller_reports import (
    get_full_election_report_data, 
    generate_csv_report, 
    generate_excel_report,
    export_full_reports  # <--- Added this import
)


class ProgressBarWidget(QWidget):
    """Custom progress bar with percentage label"""

    def __init__(self, value: float, color: str = "#10B981"):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(value))
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #E5E7EB;
                border-radius: 6px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)

        label = QLabel(f"{value:.1f}%")
        label.setFont(QFont("Segoe UI", 10))
        label.setStyleSheet("color: #374151;")
        label.setFixedWidth(50)

        layout.addWidget(bar, 1)
        layout.addWidget(label)


class AdminResultsPage(QWidget):
    """Page showing election results with charts"""

    def __init__(self):
        super().__init__()
        self.db = Database()
        self._candidates = []
        self.elections = []
        self.selector = None
        self._setup_ui()
        self._load_elections()

    def _setup_ui(self):
        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Selector row
        selector_row = QHBoxLayout()
        selector_lbl = QLabel("Select Election")
        selector_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        selector_lbl.setStyleSheet("color: #111827;")

        self.selector = QComboBox()
        self.selector.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: #FFFFFF;
                color: #111827;
                min-width: 260px;
            }
            QComboBox::drop-down { border: none; width: 22px; }
            QComboBox QAbstractItemView {
                color: #111827;
                background: #FFFFFF;
                selection-background-color: #DBEAFE;
            }
        """)
        self.selector.currentIndexChanged.connect(self._on_select_changed)

        selector_row.addWidget(selector_lbl)
        selector_row.addWidget(self.selector)
        selector_row.addStretch()

        # Generate Report button
        self.report_btn = QPushButton("📄  Generate Report")
        self.report_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.report_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.report_btn.setFixedHeight(38)
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.report_btn.clicked.connect(self._generate_report)
        selector_row.addWidget(self.report_btn)

        layout.addLayout(selector_row)

        # Title row with status
        title_row = QHBoxLayout()
        self.title_lbl = QLabel("Student Council President 2025")
        self.title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #111827;")

        self.status_badge = StatusBadge("finalized")

        title_row.addWidget(self.title_lbl)
        title_row.addWidget(self.status_badge)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Winner banner
        self.winner_banner = WinnerBanner()
        layout.addWidget(self.winner_banner)

        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)

        # Bar chart card
        bar_card = QFrame()
        bar_card.setStyleSheet("background-color: #FFFFFF; border-radius: 16px;")
        shadow1 = QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(20)
        shadow1.setColor(QColor(0, 0, 0, 15))
        shadow1.setOffset(0, 4)
        bar_card.setGraphicsEffect(shadow1)

        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(25, 20, 25, 20)

        bar_title = QLabel("Vote Distribution")
        bar_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        bar_title.setStyleSheet("color: #111827;")
        bar_layout.addWidget(bar_title)

        self.bar_chart = BarChart()
        self.bar_chart.setMinimumHeight(280)
        bar_layout.addWidget(self.bar_chart)

        charts_row.addWidget(bar_card, 2)

        # Pie chart card
        pie_card = QFrame()
        pie_card.setStyleSheet("background-color: #FFFFFF; border-radius: 16px;")
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setColor(QColor(0, 0, 0, 15))
        shadow2.setOffset(0, 4)
        pie_card.setGraphicsEffect(shadow2)

        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setContentsMargins(25, 20, 25, 20)

        pie_title = QLabel("Vote Percentage")
        pie_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        pie_title.setStyleSheet("color: #111827;")
        pie_layout.addWidget(pie_title)

        self.pie_chart = PieChart()
        self.pie_chart.setMinimumSize(300, 350)
        pie_layout.addWidget(self.pie_chart)

        charts_row.addWidget(pie_card, 1)
        layout.addLayout(charts_row)

        # Detailed results table card
        table_card = QFrame()
        table_card.setStyleSheet("background-color: #FFFFFF; border-radius: 16px;")
        shadow3 = QGraphicsDropShadowEffect()
        shadow3.setBlurRadius(20)
        shadow3.setColor(QColor(0, 0, 0, 15))
        shadow3.setOffset(0, 4)
        table_card.setGraphicsEffect(shadow3)

        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(30, 25, 30, 25)

        table_title = QLabel("Detailed Results")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_title.setStyleSheet("color: #111827;")
        table_layout.addWidget(table_title)

        self.table = DataTable(["Rank", "Candidate", "Votes", "Percentage"])
        self.table.setMinimumHeight(250)
        table_layout.addWidget(self.table)

        layout.addWidget(table_card)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_data(self, election_id: int | None = None):
        """Load results data from database"""
        try:
            self._candidates = []
            conn = self.db.get_connection()
            if not conn:
                self._show_placeholder()
                return

            cursor = conn.cursor(dictionary=True)

            if election_id is None:
                election = self._get_default_election()
            else:
                election = self.db.get_election_by_id(election_id)

            if election:
                self.title_lbl.setText(election.get('title', 'Election Results'))
                status = election.get('status', 'active')
                self.status_badge.set_status(status)

                # Get candidates with aggregated votes from voting_records
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
                    (election['election_id'],),
                )
                self._candidates = cursor.fetchall()

            cursor.close()
            conn.close()

            if self._candidates:
                self._populate_results()
            else:
                self._show_placeholder()

        except Exception as e:
            print(f"Load results error: {e}")
            self._show_placeholder()

    def _populate_results(self):
        # Normalize vote values to ints
        for c in self._candidates:
            try:
                c['votes'] = int(c.get('votes') or 0)
            except Exception:
                c['votes'] = 0

        total_votes = sum(c.get('votes', 0) for c in self._candidates)

        # Winner banner
        if self._candidates:
            winner = self._candidates[0]
            winner_votes = winner.get('votes', 0)
            winner_pct = (winner_votes / total_votes * 100) if total_votes else 0
            self.winner_banner.set_winner(winner.get('full_name', ''), winner_votes, winner_pct)

        # Charts
        chart_data = [(c.get('full_name', '').split()[-1], c.get('votes', 0))
                      for c in self._candidates]
        self.bar_chart.set_data(chart_data)
        self.pie_chart.set_data(chart_data)

        # Table
        self.table.setRowCount(len(self._candidates))

        colors = ["#10B981", "#3B82F6", "#8B5CF6", "#06B6D4", "#F59E0B"]

        for i, candidate in enumerate(self._candidates):
            votes = candidate.get('votes', 0)
            pct = (votes / total_votes * 100) if total_votes else 0

            # Rank
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, rank_item)

            # Name
            self.table.setItem(i, 1, QTableWidgetItem(candidate.get('full_name', '')))

            # Votes
            votes_item = QTableWidgetItem(str(votes))
            votes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, votes_item)

            # Percentage with progress bar
            color = colors[i % len(colors)]
            progress = ProgressBarWidget(pct, color)
            self.table.setCellWidget(i, 3, progress)

            self.table.setRowHeight(i, 50)

    def _show_placeholder(self):
        """Show placeholder data when no real data available"""
        placeholder = [
            ("Leni Lobredo", 850),
            ("Marco Santos", 327),
            ("Sarah Johnson", 131),
            ("Alex Chen", 85),
        ]

        total = sum(v for _, v in placeholder)
        self.winner_banner.set_winner(placeholder[0][0], placeholder[0][1],
                                      placeholder[0][1] / total * 100)

        self.bar_chart.set_data(placeholder)
        self.pie_chart.set_data(placeholder)

        self.table.setRowCount(len(placeholder))
        colors = ["#10B981", "#3B82F6", "#8B5CF6", "#06B6D4"]

        for i, (name, votes) in enumerate(placeholder):
            pct = votes / total * 100

            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, rank_item)

            self.table.setItem(i, 1, QTableWidgetItem(name))

            votes_item = QTableWidgetItem(str(votes))
            votes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, votes_item)

            progress = ProgressBarWidget(pct, colors[i % len(colors)])
            self.table.setCellWidget(i, 3, progress)

            self.table.setRowHeight(i, 50)

    def refresh(self):
        self._load_data()

    def _load_elections(self):
        self.elections = self.db.get_all_elections()
        self.selector.blockSignals(True)
        self.selector.clear()
        for e in self.elections:
            start = e.get("start_date")
            end = e.get("end_date")
            date_str = "" if not start and not end else f" ({start} - {end})"
            status = (e.get("status") or "").upper()
            label = f"{e.get('title', 'Election')} [{status}]{date_str}"
            self.selector.addItem(label)
        self.selector.blockSignals(False)

        default = self._get_default_election()
        if default:
            idx = self.elections.index(default)
            self.selector.setCurrentIndex(idx)
            self._load_data(default.get("election_id"))
        else:
            self._load_data(None)

    def _get_default_election(self):
        if not self.elections:
            return None
        active = [e for e in self.elections if (e.get("status") or "").lower() == "active"]
        if active:
            return active[0]
        with_candidates = [e for e in self.elections if (e.get("candidate_count") or 0) > 0]
        return with_candidates[0] if with_candidates else self.elections[0]

    def _on_select_changed(self, idx: int):
        if idx < 0 or idx >= len(self.elections):
            return
        election = self.elections[idx]
        self._load_data(election.get("election_id"))

    def _generate_report(self):
        """Show menu to choose report format"""
        menu = QMenu(self)
        menu.setStyleSheet("""
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
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #D1FAE5;
                color: #065F46;
            }
            QMenu::separator {
                height: 1px;
                background: #E5E7EB;
                margin: 5px 0;
            }
        """)
        
        # --- NEW FULL DETAIL REPORT BUTTON ---
        full_action = menu.addAction("🚀  Generate Full Detail Report (PDF + Bundle)")
        full_action.triggered.connect(self._export_full_detail)
        
        menu.addSeparator()

        csv_action = menu.addAction("📄  Export as CSV Files Only")
        csv_action.triggered.connect(self._export_csv)
        
        excel_action = menu.addAction("📊  Export as Excel File Only")
        excel_action.triggered.connect(self._export_excel)
        
        menu.exec(self.report_btn.mapToGlobal(self.report_btn.rect().bottomLeft()))

    def _export_full_detail(self):
        """Handler for the new Full Detail Report button"""
        idx = self.selector.currentIndex()
        if idx < 0 or idx >= len(self.elections):
            QMessageBox.warning(self, "No Election", "Please select an election first.")
            return

        election = self.elections[idx]
        election_id = election.get("election_id")
        title = election.get("title", "Election").replace(" ", "_")
        
        default_name = f"Full_Report_{title}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Full Report Bundle",
            default_name,
            "Report Bundle (*)" # User selects base name, logic adds extensions
        )

        if file_path:
            self.setCursor(Qt.CursorShape.WaitCursor)
            
            # This calls the controller function that generates PDF + Excel + CSV
            success, message = export_full_reports(election_id, file_path)
            
            self.setCursor(Qt.CursorShape.ArrowCursor)

            if success:
                QMessageBox.information(
                    self, 
                    "Reports Generated Successfully", 
                    f"Reports created:\n"
                    f"✅ Full Detail PDF\n"
                    f"✅ Excel Workbook\n"
                    f"✅ Raw Data CSVs\n\n"
                    f"Location: {os.path.dirname(file_path)}"
                )
                try:
                    os.startfile(os.path.dirname(file_path))
                except Exception:
                    pass
            else:
                QMessageBox.critical(self, "Generation Failed", message)

    def _export_csv(self):
        """Export full raw data as CSV files"""
        idx = self.selector.currentIndex()
        if idx < 0 or idx >= len(self.elections):
            QMessageBox.warning(self, "No Election", "Please select an election first.")
            return

        election = self.elections[idx]
        election_id = election.get("election_id")
        election_title = election.get("title", "Election").replace(" ", "_")

        report_data = get_full_election_report_data(election_id)

        if not report_data.get("success"):
            QMessageBox.warning(self, "Error", report_data.get("error", "Failed to get report data."))
            return

        default_name = f"Election_Report_{election_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Report",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            success, message = generate_csv_report(report_data, file_path)
            if success:
                QMessageBox.information(
                    self,
                    "CSV Reports Generated",
                    f"Full election data exported successfully!\n\n{message}"
                )
                try:
                    os.startfile(os.path.dirname(file_path))
                except Exception:
                    pass
            else:
                QMessageBox.critical(self, "Error", message)

    def _export_excel(self):
        """Export full raw data as Excel file"""
        idx = self.selector.currentIndex()
        if idx < 0 or idx >= len(self.elections):
            QMessageBox.warning(self, "No Election", "Please select an election first.")
            return

        election = self.elections[idx]
        election_id = election.get("election_id")
        election_title = election.get("title", "Election").replace(" ", "_")

        report_data = get_full_election_report_data(election_id)

        if not report_data.get("success"):
            QMessageBox.warning(self, "Error", report_data.get("error", "Failed to get report data."))
            return

        default_name = f"Election_Report_{election_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel Report",
            default_name,
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if file_path:
            success, message = generate_excel_report(report_data, file_path)
            if success:
                QMessageBox.information(
                    self,
                    "Excel Report Generated",
                    f"Full election data exported successfully!\n\n{message}"
                )
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
            else:
                QMessageBox.critical(self, "Error", message)
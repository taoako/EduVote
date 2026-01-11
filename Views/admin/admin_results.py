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
        self._position_results: dict | None = None
        self.elections = []
        self.selector = None
        self._chart_mode = "results"
        self._current_election_id: int | None = None
        self._view_mode = "overall"  # overall | position_winner | position_tally
        self._positions_for_tally: list[dict] = []
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

        # View mode selector (overall vs by-position)
        view_lbl = QLabel("View")
        view_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        view_lbl.setStyleSheet("color: #111827;")

        self.view_combo = QComboBox()
        self.view_combo.addItem("Overall", "overall")
        self.view_combo.addItem("By Position (Winner)", "position_winner")
        self.view_combo.addItem("By Position (Tally)", "position_tally")
        self.view_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: #FFFFFF;
                color: #111827;
                min-width: 210px;
            }
            QComboBox::drop-down { border: none; width: 22px; }
            QComboBox QAbstractItemView {
                color: #111827;
                background: #FFFFFF;
                selection-background-color: #DBEAFE;
            }
        """)
        self.view_combo.currentIndexChanged.connect(self._on_view_mode_changed)

        selector_row.addSpacing(10)
        selector_row.addWidget(view_lbl)
        selector_row.addWidget(self.view_combo)
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

        # Position selector (only visible in tally mode)
        position_row = QHBoxLayout()
        self.position_lbl = QLabel("Position")
        self.position_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.position_lbl.setStyleSheet("color: #111827;")

        self.position_combo = QComboBox()
        self.position_combo.setStyleSheet("""
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
        self.position_combo.currentIndexChanged.connect(self._on_position_selected)

        position_row.addWidget(self.position_lbl)
        position_row.addWidget(self.position_combo)
        position_row.addStretch(1)

        self.position_row_widget = QWidget()
        self.position_row_widget.setLayout(position_row)
        self.position_row_widget.setVisible(False)
        layout.addWidget(self.position_row_widget)

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

        bar_header = QHBoxLayout()
        self.bar_title = QLabel("Vote Distribution")
        self.bar_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.bar_title.setStyleSheet("color: #111827;")
        bar_header.addWidget(self.bar_title)
        bar_header.addStretch(1)

        self.chart_mode_combo = QComboBox()
        self.chart_mode_combo.addItem("Live Results", "results")
        self.chart_mode_combo.addItem("Turnout by Position", "position_turnout")
        self.chart_mode_combo.addItem("Turnout by Grade/Section (%)", "grade_section_turnout")
        self.chart_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 6px 10px;
                color: #111827;
                font-size: 12px;
                font-family: 'Segoe UI';
                min-width: 210px;
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
        self.chart_mode_combo.currentIndexChanged.connect(self._on_chart_mode_changed)
        bar_header.addWidget(self.chart_mode_combo)
        bar_layout.addLayout(bar_header)

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

        self.pie_title = QLabel("Vote Percentage")
        self.pie_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.pie_title.setStyleSheet("color: #111827;")
        pie_layout.addWidget(self.pie_title)

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
            self._position_results = None
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
                self._current_election_id = election.get('election_id')
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

            # Apply view + chart mode after base results/placeholder are rendered.
            self._refresh_view()

        except Exception as e:
            print(f"Load results error: {e}")
            self._show_placeholder()
            self._refresh_view()

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

    def _on_view_mode_changed(self, _index: int):
        self._view_mode = self.view_combo.currentData() or "overall"
        self._refresh_view()

    def _on_position_selected(self, _index: int):
        if (self._view_mode or "overall") != "position_tally":
            return
        self._refresh_view()

    def _refresh_view(self):
        # Default visibility/state
        mode = self._view_mode or "overall"
        self.position_row_widget.setVisible(mode == "position_tally")

        # Keep chart-mode selector relevant: only used for overall view.
        if mode == "overall":
            self.chart_mode_combo.setEnabled(True)
            self.winner_banner.setVisible(True)
            # Restore overall table headers
            self.table.clear()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Rank", "Candidate", "Votes", "Percentage"])
            self._update_charts_for_mode()
            return

        # For position views, keep charts on the selected position/winners and disable chart-mode combo.
        self.chart_mode_combo.setEnabled(False)
        self.chart_mode_combo.setCurrentIndex(0)  # Live Results
        self._chart_mode = "results"

        if not self._current_election_id:
            return

        try:
            self._position_results = self.db.get_election_results_by_position(self._current_election_id)
        except Exception as e:
            print(f"Position results load error: {e}")
            self._position_results = None
            return

        positions = (self._position_results or {}).get('positions') or []
        if mode == "position_winner":
            self._render_position_winners(positions)
        else:
            self._render_position_tally(positions)

    def _render_position_winners(self, positions: list[dict]):
        self.winner_banner.setVisible(False)

        self.bar_title.setText("Position Winners")
        self.pie_title.setText("Position Winners")

        # Table: Position | Winner | Votes | Percentage
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Position", "Winner", "Votes", "Percentage"])

        rows = []
        chart_data = []
        for entry in positions:
            pos = (entry.get('position') or {})
            pos_title = (pos.get('title') or "General")

            total_votes = int(entry.get('total_votes') or 0)
            winner = entry.get('winner')
            if not winner:
                rows.append((pos_title, "—", 0, 0.0))
                chart_data.append((pos_title, 0))
                continue

            winner_name = winner.get('full_name') or "—"
            winner_votes = int(winner.get('vote_count') or 0)
            pct = (winner_votes / total_votes * 100) if total_votes else 0.0
            rows.append((pos_title, winner_name, winner_votes, pct))
            chart_data.append((pos_title, winner_votes))

        self.table.setRowCount(len(rows))
        for i, (pos_title, name, votes, pct) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(pos_title)))
            self.table.setItem(i, 1, QTableWidgetItem(str(name)))

            votes_item = QTableWidgetItem(str(votes))
            votes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, votes_item)

            progress = ProgressBarWidget(pct, "#10B981")
            self.table.setCellWidget(i, 3, progress)
            self.table.setRowHeight(i, 50)

        self.bar_chart.set_data(chart_data)
        self.pie_chart.set_data(chart_data)

    def _render_position_tally(self, positions: list[dict]):
        self.winner_banner.setVisible(True)

        # Populate position combo, but preserve selection.
        prev_selected_pid = self.position_combo.currentData()

        new_positions = []
        for entry in positions:
            pos = (entry.get('position') or {})
            new_positions.append({
                "position_id": pos.get('position_id'),
                "title": (pos.get('title') or "General")
            })

        if new_positions != self._positions_for_tally:
            self._positions_for_tally = new_positions
            self.position_combo.blockSignals(True)
            self.position_combo.clear()
            for p in self._positions_for_tally:
                self.position_combo.addItem(p["title"], p["position_id"])

            # Restore previous selection if possible.
            if prev_selected_pid is not None:
                for i in range(self.position_combo.count()):
                    if self.position_combo.itemData(i) == prev_selected_pid:
                        self.position_combo.setCurrentIndex(i)
                        break

            self.position_combo.blockSignals(False)

        selected_pid = self.position_combo.currentData()
        selected_entry = None
        for entry in positions:
            pos = (entry.get('position') or {})
            if pos.get('position_id') == selected_pid:
                selected_entry = entry
                break

        if not selected_entry and positions:
            # Default to first (avoid triggering recursion)
            self.position_combo.blockSignals(True)
            self.position_combo.setCurrentIndex(0)
            self.position_combo.blockSignals(False)
            selected_entry = positions[0]

        if not selected_entry:
            return

        pos = (selected_entry.get('position') or {})
        pos_title = (pos.get('title') or "General")

        candidates = selected_entry.get('candidates') or []
        total_votes = int(selected_entry.get('total_votes') or 0)

        # Winner banner for this position
        winner = selected_entry.get('winner')
        if winner:
            w_votes = int(winner.get('vote_count') or 0)
            w_pct = (w_votes / total_votes * 100) if total_votes else 0.0
            self.winner_banner.set_winner(winner.get('full_name', ''), w_votes, w_pct)
        else:
            self.winner_banner.set_winner("No winner yet", 0, 0.0)

        self.bar_title.setText(f"Tally: {pos_title}")
        self.pie_title.setText(f"Tally: {pos_title}")

        chart_data = [(c.get('full_name', '').split()[-1], int(c.get('vote_count') or 0)) for c in candidates]
        self.bar_chart.set_data(chart_data)
        self.pie_chart.set_data(chart_data)

        # Table back to candidate format
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rank", "Candidate", "Votes", "Percentage"])
        self.table.setRowCount(len(candidates))

        colors = ["#10B981", "#3B82F6", "#8B5CF6", "#06B6D4", "#F59E0B"]
        for i, c in enumerate(candidates):
            votes = int(c.get('vote_count') or 0)
            pct = (votes / total_votes * 100) if total_votes else 0.0

            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, rank_item)
            self.table.setItem(i, 1, QTableWidgetItem(c.get('full_name', '')))

            votes_item = QTableWidgetItem(str(votes))
            votes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, votes_item)

            progress = ProgressBarWidget(pct, colors[i % len(colors)])
            self.table.setCellWidget(i, 3, progress)
            self.table.setRowHeight(i, 50)

    def _on_chart_mode_changed(self, _index: int):
        self._chart_mode = self.chart_mode_combo.currentData() or "results"
        self._update_charts_for_mode()

    def _update_charts_for_mode(self):
        # If we don't have a real election selected yet, keep whatever is currently shown.
        if not self._current_election_id:
            return

        if (self._chart_mode or "results") == "results":
            self.bar_title.setText("Vote Distribution")
            self.pie_title.setText("Vote Percentage")

            # Use the already-loaded candidate rows for charts (keeps consistent with table).
            chart_data = [
                (c.get('full_name', '').split()[-1], int(c.get('votes') or 0))
                for c in (self._candidates or [])
            ]
            self.bar_chart.set_data(chart_data)
            self.pie_chart.set_data(chart_data)
            return

        try:
            info = self.db.get_election_chart_data(self._current_election_id, mode=self._chart_mode)
            data = info.get('data', [])

            if self._chart_mode == "position_turnout":
                self.bar_title.setText("Turnout by Position")
                self.pie_title.setText("Turnout by Position")
            else:
                self.bar_title.setText("Turnout (%)")
                self.pie_title.setText("Turnout (%)")

            self.bar_chart.set_data(data)
            self.pie_chart.set_data(data)
        except Exception as e:
            print(f"Chart mode load error: {e}")

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
            # Attach admin name for report attribution (Prepared by)
            admin_name = None
            try:
                w = self.window()
                if w is not None and hasattr(w, "user_data"):
                    ud = getattr(w, "user_data") or {}
                    admin_name = ud.get("name") or ud.get("full_name") or ud.get("username")
            except Exception:
                admin_name = None

            success, message = export_full_reports(election_id, file_path, prepared_by=admin_name)
            
            self.setCursor(Qt.CursorShape.ArrowCursor)

            if success:
                QMessageBox.information(
                    self, 
                    "Reports Generated Successfully", 
                    f"Reports created:\n"
                    f"✅ Full Detail PDF\n"
                    f"✅ Excel Workbook\n"
                    f"✅ Raw Data CSV\n\n"
                    f"{message}\n\n"
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
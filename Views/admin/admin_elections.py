from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QTableWidgetItem, QDialog,
    QLineEdit, QDateEdit, QComboBox, QMessageBox, QPushButton,
    QScrollArea, QCheckBox, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from .admin_components import GreenButton, DataTable, StatusBadge, ActionButton, SearchBar
from Controller.controller_elections import (
    list_elections,
    list_candidates,
    create_election,
    update_election,
    delete_election,
    set_election_status,
    get_positions_for_election,
    create_position,
    delete_position,
    get_election_ballot_data,
)
from Controller.controller_candidates import list_candidates as list_all_candidates
from Controller.controller_voters import list_sections as list_sections_lookup, add_section as add_new_section


class CandidateSelectCard(QFrame):
    """Clickable candidate card for selection in position assignment."""
    toggled = pyqtSignal(int, bool)  # candidate_id, is_selected

    def __init__(self, candidate: dict, is_selected: bool = False):
        super().__init__()
        self.candidate = candidate
        self.candidate_id = candidate.get('candidate_id')
        self._selected = is_selected
        self.setFixedSize(170, 80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Avatar circle
        colors = ["#F59E0B", "#06B6D4", "#8B5CF6", "#3B82F6", "#EC4899", "#10B981"]
        color = colors[self.candidate_id % len(colors)] if self.candidate_id else "#9CA3AF"
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 20px;
            }}
        """)
        layout.addWidget(avatar)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name = QLabel(candidate.get('full_name', 'Unknown')[:18])
        name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name.setStyleSheet("color: #111827; background: transparent;")
        info_layout.addWidget(name)

        slogan = candidate.get('slogan', '')[:25]
        if slogan:
            slogan_lbl = QLabel(slogan)
            slogan_lbl.setFont(QFont("Segoe UI", 8))
            slogan_lbl.setStyleSheet("color: #6B7280; background: transparent;")
            info_layout.addWidget(slogan_lbl)

        layout.addLayout(info_layout)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet("""
                CandidateSelectCard {
                    background: #D1FAE5;
                    border: 2px solid #10B981;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                CandidateSelectCard {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                }
                CandidateSelectCard:hover {
                    border: 1px solid #10B981;
                }
            """)

    def mousePressEvent(self, event):
        self._selected = not self._selected
        self._update_style()
        self.toggled.emit(self.candidate_id, self._selected)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()


class PositionWidget(QFrame):
    """Widget for managing a single position with its candidates."""
    remove_clicked = pyqtSignal(object)  # self
    candidates_changed = pyqtSignal()

    def __init__(self, position_title: str = "", all_candidates: list = None, selected_candidate_ids: list = None, position_id: int = None):
        super().__init__()
        self.position_id = position_id
        self.all_candidates = all_candidates or []
        self.selected_candidate_ids = set(selected_candidate_ids or [])
        self._candidate_cards = []

        self.setStyleSheet("""
            PositionWidget {
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Header row with title input and remove button
        header = QHBoxLayout()
        header.setSpacing(10)

        title_label = QLabel("Position Title")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #374151; background: transparent;")
        header.addWidget(title_label)

        self.title_input = QLineEdit(position_title)
        self.title_input.setPlaceholderText("e.g., President, Vice President, Secretary")
        self.title_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 8px 12px;
                background: #FFFFFF;
                color: #111827;
            }
            QLineEdit:focus {
                border: 2px solid #10B981;
            }
        """)
        self.title_input.setFixedHeight(40)
        header.addWidget(self.title_input, 1)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(32, 32)
        remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #FEE2E2;
                border: none;
                border-radius: 16px;
                color: #DC2626;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #FECACA;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self))
        header.addWidget(remove_btn)

        layout.addLayout(header)

        # Candidates label
        cand_label = QLabel("Select Candidates")
        cand_label.setFont(QFont("Segoe UI", 10))
        cand_label.setStyleSheet("color: #6B7280; background: transparent;")
        layout.addWidget(cand_label)

        # Candidates grid in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        grid_container = QWidget()
        self.candidates_grid = QGridLayout(grid_container)
        self.candidates_grid.setSpacing(10)
        self.candidates_grid.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(grid_container)
        layout.addWidget(scroll)

        self._populate_candidates()

    def _populate_candidates(self):
        # Clear existing
        while self.candidates_grid.count():
            item = self.candidates_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._candidate_cards.clear()

        row, col = 0, 0
        max_cols = 3
        for candidate in self.all_candidates:
            cid = candidate.get('candidate_id')
            is_selected = cid in self.selected_candidate_ids
            card = CandidateSelectCard(candidate, is_selected)
            card.toggled.connect(self._on_candidate_toggled)
            self._candidate_cards.append(card)
            self.candidates_grid.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.all_candidates:
            placeholder = QLabel("No candidates available. Create candidates first.")
            placeholder.setStyleSheet("color: #9CA3AF; font-size: 11px; background: transparent;")
            self.candidates_grid.addWidget(placeholder, 0, 0)

    def _on_candidate_toggled(self, candidate_id: int, is_selected: bool):
        if is_selected:
            self.selected_candidate_ids.add(candidate_id)
        else:
            self.selected_candidate_ids.discard(candidate_id)
        self.candidates_changed.emit()

    def get_data(self) -> dict:
        return {
            "position_id": self.position_id,
            "title": self.title_input.text().strip(),
            "candidate_ids": list(self.selected_candidate_ids)
        }

    def update_candidates(self, all_candidates: list):
        """Update available candidates list."""
        self.all_candidates = all_candidates
        self._populate_candidates()


class ElectionDialog(QDialog):
    """Dialog for creating/editing an election with positions and candidates."""

    def __init__(self, parent=None, election: dict = None):
        super().__init__(parent)
        self.election = election
        self.sections = list_sections_lookup() or []
        self.adding_new_section = False
        self.position_widgets = []
        self.all_candidates = list_all_candidates() or []

        self.setWindowTitle("Edit Election" if election else "Create New Election")
        self.setMinimumSize(700, 580)
        self.setMaximumHeight(650)
        self.resize(700, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: #FFFFFF;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(14)

        # Title
        title = QLabel("Edit Election" if election else "Create New Election")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        content_layout.addWidget(title)

        # Form styles
        form_style = """
            QLineEdit, QDateEdit, QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #111827;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border: 2px solid #10B981;
            }
            QCalendarWidget QWidget { background: #FFFFFF; color: #111827; }
            QCalendarWidget QToolButton { background: transparent; color: #111827; font-weight: 600; border: none; padding: 6px; }
            QCalendarWidget QAbstractItemView { selection-background-color: #D1FAE5; selection-color: #065F46; background: #FFFFFF; color: #111827; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; border: 1px solid #D1D5DB; color: #111827; }
            QComboBox QAbstractItemView::item:selected { background-color: #E5E7EB; color: #111827; }
        """

        label_style = "color: #374151; font-size: 13px; font-weight: 600;"

        # Election Title
        title_label = QLabel("Election Title")
        title_label.setStyleSheet(label_style)
        content_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Student Council 2025")
        self.title_input.setStyleSheet(form_style)
        self.title_input.setFixedHeight(40)
        content_layout.addWidget(self.title_input)

        # Date row
        date_row = QHBoxLayout()
        date_row.setSpacing(20)

        start_col = QVBoxLayout()
        start_col.setSpacing(8)
        start_label = QLabel("Start Date")
        start_label.setStyleSheet(label_style)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setStyleSheet(form_style)
        self.start_date.setFixedHeight(40)
        start_col.addWidget(start_label)
        start_col.addWidget(self.start_date)

        end_col = QVBoxLayout()
        end_col.setSpacing(8)
        end_label = QLabel("End Date")
        end_label.setStyleSheet(label_style)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(7))
        self.end_date.setStyleSheet(form_style)
        self.end_date.setFixedHeight(40)
        end_col.addWidget(end_label)
        end_col.addWidget(self.end_date)

        date_row.addLayout(start_col, 1)
        date_row.addLayout(end_col, 1)
        content_layout.addLayout(date_row)

        # Positions & Candidates section
        pos_header = QHBoxLayout()
        pos_label = QLabel("Positions & Candidates")
        pos_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        pos_label.setStyleSheet("color: #111827;")
        pos_header.addWidget(pos_label)
        pos_header.addStretch()

        add_pos_btn = QPushButton("+ Add Position")
        add_pos_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_pos_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        add_pos_btn.clicked.connect(self._add_position)
        pos_header.addWidget(add_pos_btn)
        content_layout.addLayout(pos_header)

        # Positions container
        self.positions_container = QVBoxLayout()
        self.positions_container.setSpacing(15)
        content_layout.addLayout(self.positions_container)

        # Scope section
        scope_label = QLabel("Eligible Audience")
        scope_label.setStyleSheet(label_style)
        content_layout.addWidget(scope_label)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["All Students", "Specific Grade", "Specific Section"])
        self.scope_combo.setStyleSheet(form_style)
        self.scope_combo.setFixedHeight(40)
        content_layout.addWidget(self.scope_combo)

        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(form_style)
        self.grade_combo.setFixedHeight(40)
        self.grade_combo.setVisible(False)
        content_layout.addWidget(self.grade_combo)

        self.section_combo = QComboBox()
        self.section_combo.setStyleSheet(form_style)
        self.section_combo.setFixedHeight(40)
        self.section_combo.setVisible(False)
        content_layout.addWidget(self.section_combo)

        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        self.grade_combo.currentIndexChanged.connect(self._on_grade_changed)
        self._populate_grade_options()

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)

        # Button row - fixed at bottom, not inside scroll
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E5E7EB;")
        btn_frame.setFixedHeight(70)
        
        btn_row = QHBoxLayout(btn_frame)
        btn_row.setContentsMargins(30, 12, 30, 12)
        btn_row.setSpacing(15)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(42)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFont(QFont("Segoe UI", 12))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F3F4F6;
                border: 2px solid #E5E7EB;
                border-radius: 21px;
                padding: 8px 28px;
                color: #6B7280;
                font-weight: 600;
            }
            QPushButton:hover { background: #E5E7EB; color: #374151; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Create Election" if not election else "Save Election")
        save_btn.setFixedHeight(42)
        save_btn.setMinimumWidth(150)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 21px;
                padding: 8px 28px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        save_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addWidget(btn_frame)

        # Pre-fill if editing
        if election:
            self._prefill_election(election)
        else:
            # Add one default position
            self._add_position()

        self.start_date.dateChanged.connect(self._sync_end_date_min)
        self._sync_end_date_min(self.start_date.date())

    def _add_position(self):
        """Add a new position widget."""
        pos_widget = PositionWidget(
            position_title="",
            all_candidates=self.all_candidates,
            selected_candidate_ids=[]
        )
        pos_widget.remove_clicked.connect(self._remove_position)
        self.position_widgets.append(pos_widget)
        self.positions_container.addWidget(pos_widget)

    def _remove_position(self, widget: PositionWidget):
        """Remove a position widget."""
        if len(self.position_widgets) <= 1:
            QMessageBox.warning(self, "Cannot Remove", "At least one position is required.")
            return
        self.position_widgets.remove(widget)
        self.positions_container.removeWidget(widget)
        widget.deleteLater()

    def _prefill_election(self, election: dict):
        """Pre-fill form with existing election data."""
        self.title_input.setText(election.get('title', ''))
        if election.get('start_date'):
            self.start_date.setDate(QDate.fromString(str(election['start_date']), "yyyy-MM-dd"))
        if election.get('end_date'):
            self.end_date.setDate(QDate.fromString(str(election['end_date']), "yyyy-MM-dd"))

        # Load existing positions
        election_id = election.get('election_id')
        if election_id:
            ballot_data = get_election_ballot_data(election_id)
            positions = ballot_data.get('positions', [])
            for pos_data in positions:
                pos = pos_data.get('position', {})
                candidates = pos_data.get('candidates', [])
                if pos.get('position_id') is None:
                    continue  # Skip "General" placeholder
                pos_widget = PositionWidget(
                    position_title=pos.get('title', ''),
                    all_candidates=self.all_candidates,
                    selected_candidate_ids=[c.get('candidate_id') for c in candidates],
                    position_id=pos.get('position_id')
                )
                pos_widget.remove_clicked.connect(self._remove_position)
                self.position_widgets.append(pos_widget)
                self.positions_container.addWidget(pos_widget)

        # Add default position if none exist
        if not self.position_widgets:
            self._add_position()

        # Prefill scope
        allowed_grade = election.get('allowed_grade')
        allowed_section = election.get('allowed_section')
        self._prefill_scope(allowed_grade, allowed_section)

    def _sync_end_date_min(self, start: QDate):
        try:
            self.end_date.setMinimumDate(start)
            if self.end_date.date() < start:
                self.end_date.setDate(start)
        except Exception:
            pass

    def accept(self):
        # Validate
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Election title is required.")
            return

        # Validate positions
        for pos_widget in self.position_widgets:
            data = pos_widget.get_data()
            if not data['title']:
                QMessageBox.warning(self, "Validation Error", "All positions must have a title.")
                return

        super().accept()

    def _on_scope_changed(self, index: int):
        scope = self.scope_combo.currentText()
        show_grade = scope in ("Specific Grade", "Specific Section")
        show_section = scope == "Specific Section"
        self.grade_combo.setVisible(show_grade)
        self.section_combo.setVisible(show_section)

    def _populate_grade_options(self):
        self.grade_combo.blockSignals(True)
        self.grade_combo.clear()
        self.grade_combo.addItem("Select grade", None)
        grades = sorted({s.get('grade_level') for s in self.sections if s.get('grade_level') is not None})
        for grade in grades:
            self.grade_combo.addItem(str(grade), grade)
        self.grade_combo.blockSignals(False)

    def _populate_section_options(self, grade_level):
        self.section_combo.clear()
        self.section_combo.addItem("Select section", None)
        if grade_level is None:
            return
        for s in self.sections:
            if s.get('grade_level') == grade_level:
                self.section_combo.addItem(s.get('section_name'), s.get('section_name'))

    def _on_grade_changed(self, index: int):
        grade_level = self.grade_combo.currentData()
        self._populate_section_options(grade_level)

    def _prefill_scope(self, allowed_grade, allowed_section):
        if allowed_grade is None and not allowed_section:
            self.scope_combo.setCurrentText("All Students")
            return

        target_scope = "Specific Section" if allowed_section else "Specific Grade"
        self.scope_combo.setCurrentText(target_scope)
        self._on_scope_changed(self.scope_combo.currentIndex())

        if allowed_grade is not None:
            idx = self.grade_combo.findData(allowed_grade)
            if idx != -1:
                self.grade_combo.setCurrentIndex(idx)
                self._populate_section_options(allowed_grade)

        if allowed_section:
            sidx = self.section_combo.findData(allowed_section)
            if sidx != -1:
                self.section_combo.setCurrentIndex(sidx)

    def get_data(self) -> dict:
        """Get form data including positions."""
        scope = self.scope_combo.currentText()
        allowed_grade = None
        allowed_section = None

        if scope == "Specific Grade":
            allowed_grade = self.grade_combo.currentData()
        elif scope == "Specific Section":
            allowed_grade = self.grade_combo.currentData()
            allowed_section = self.section_combo.currentData()

        positions_data = [pw.get_data() for pw in self.position_widgets]

        return {
            'title': self.title_input.text().strip(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'status': self.election.get('status', 'upcoming') if self.election else 'upcoming',
            'allowed_grade': allowed_grade,
            'allowed_section': allowed_section,
            'positions': positions_data,
        }


class ManageElectionsPage(QWidget):
    """Page for managing elections with positions."""

    def __init__(self):
        super().__init__()
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

        title = QLabel("All Elections")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")

        self.search_bar = SearchBar("Search elections...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.textChanged.connect(self._filter_elections)

        create_btn = GreenButton("Create New Election")
        create_btn.clicked.connect(self._create_election)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.search_bar)
        header_row.addSpacing(15)
        header_row.addWidget(create_btn)
        card_layout.addLayout(header_row)

        # Table
        self.table = DataTable(["Title", "Start Date", "End Date", "Status", "Positions", "Actions"])
        card_layout.addWidget(self.table, 1)

        layout.addWidget(card)

    def _load_data(self):
        """Load elections from database."""
        try:
            self._elections = list_elections()
            # Load position counts for each election
            for election in self._elections:
                eid = election.get('election_id')
                positions = get_positions_for_election(eid) if eid else []
                election['position_count'] = len(positions)
            self._filter_elections()
        except Exception as e:
            print(f"Load elections error: {e}")

    def _filter_elections(self):
        """Filter elections based on search text."""
        search_text = self.search_bar.text().lower().strip()
        filtered = [
            e for e in self._elections
            if search_text in e.get('title', '').lower() or
               search_text in e.get('status', '').lower()
        ]
        self._populate_table(filtered)

    def _populate_table(self, elections=None):
        data = elections if elections is not None else self._elections
        self.table.setRowCount(len(data))

        for row, election in enumerate(data):
            # Title
            self.table.setItem(row, 0, QTableWidgetItem(election.get('title', '')))

            # Dates
            start = str(election.get('start_date', ''))[:10]
            end = str(election.get('end_date', ''))[:10]
            self.table.setItem(row, 1, QTableWidgetItem(start))
            self.table.setItem(row, 2, QTableWidgetItem(end))

            # Status badge
            status = election.get('status') or 'upcoming'
            badge = StatusBadge(status)
            self.table.setCellWidget(row, 3, badge)

            # Positions count
            pos_count = election.get('position_count', 0)
            positions_widget = QLabel(f"📋 {pos_count} positions")
            positions_widget.setFont(QFont("Segoe UI", 10))
            positions_widget.setStyleSheet("color: #10B981;")
            self.table.setCellWidget(row, 4, positions_widget)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(8)

            pause_btn = ActionButton("pause" if status == 'active' else "play")
            edit_btn = ActionButton("edit")
            delete_btn = ActionButton("delete")
            delete_btn.setEnabled(False)
            delete_btn.setToolTip("Deleting elections is disabled. Finalize instead.")

            election_id = election.get('election_id')
            edit_btn.clicked.connect(lambda checked, eid=election_id: self._edit_election(eid))
            pause_btn.clicked.connect(lambda checked, eid=election_id, st=status: self._toggle_status(eid, st))

            actions_layout.addWidget(pause_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 5, actions_widget)

        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 55)

    def _create_election(self):
        """Open dialog to create a new election with positions."""
        dialog = ElectionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            positions_data = data.pop('positions', [])

            if not data['title']:
                QMessageBox.warning(self, "Error", "Title is required")
                return

            # Create the election
            ok, msg = create_election(data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
                return

            # Get the newly created election ID
            elections = list_elections()
            new_election = next((e for e in elections if e.get('title') == data['title']), None)
            if new_election:
                election_id = new_election.get('election_id')
                self._save_positions(election_id, positions_data)

            self._load_data()

    def _edit_election(self, election_id: int):
        """Open dialog to edit an existing election."""
        election = next((e for e in self._elections if e['election_id'] == election_id), None)
        if not election:
            return

        dialog = ElectionDialog(self, election)
        if dialog.exec():
            data = dialog.get_data()
            positions_data = data.pop('positions', [])

            ok, msg = update_election(election_id, data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
                return

            # Update positions
            self._save_positions(election_id, positions_data)
            self._load_data()

    def _save_positions(self, election_id: int, positions_data: list):
        """Save positions and candidate assignments for an election."""
        from Models.model_db import Database
        db = Database()

        # Get existing positions
        existing_positions = get_positions_for_election(election_id)
        existing_ids = {p['position_id'] for p in existing_positions}

        new_position_ids = set()
        for idx, pos_data in enumerate(positions_data):
            pos_id = pos_data.get('position_id')
            title = pos_data.get('title', '')
            candidate_ids = pos_data.get('candidate_ids', [])

            if pos_id and pos_id in existing_ids:
                # Update existing position
                from Controller.controller_elections import update_position
                update_position(pos_id, title, idx)
                new_position_ids.add(pos_id)
            else:
                # Create new position
                ok, msg, new_pos_id = create_position(election_id, title, idx)
                if ok and new_pos_id:
                    pos_id = new_pos_id
                    new_position_ids.add(pos_id)

            # Assign candidates to position
            if pos_id:
                for cid in candidate_ids:
                    db.assign_candidate_to_position(cid, pos_id)

        # Delete removed positions
        for old_id in existing_ids - new_position_ids:
            delete_position(old_id)

    def _toggle_status(self, election_id: int, current_status: str):
        """Toggle election status between active and upcoming."""
        if current_status == 'active':
            target = 'upcoming'
        elif current_status == 'finalized':
            QMessageBox.information(self, "Info", "Finalized elections cannot be reactivated.")
            return
        else:
            target = 'active'

        ok, msg = set_election_status(election_id, target)
        if not ok:
            QMessageBox.warning(self, "Error", msg)
        else:
            self._load_data()

    def refresh(self):
        """Refresh the elections list."""
        self._load_data()

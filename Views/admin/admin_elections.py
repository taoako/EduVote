from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QTableWidgetItem, QDialog,
    QLineEdit, QDateEdit, QComboBox, QMessageBox, QPushButton,
    QScrollArea, QCheckBox, QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt, QDate

from .admin_components import GreenButton, DataTable, StatusBadge, ActionButton, SearchBar
from Controller.controller_elections import (
    list_elections,
    list_candidates,
    create_election,
    update_election,
    delete_election,
    set_election_status,
)
from Controller.controller_voters import list_sections as list_sections_lookup, add_section as add_new_section


class ElectionDialog(QDialog):
    """Dialog for creating/editing an election"""

    def __init__(self, parent=None, election: dict = None):
        super().__init__(parent)
        self.election = election
        self.selected_candidates = []
        self._candidate_checkboxes = []
        self.sections = list_sections_lookup() or []
        self.adding_new_section = False
        self.setWindowTitle("Edit Election" if election else "Create New Election")
        self.setFixedSize(620, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(18)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Title
        title = QLabel("Edit Election" if election else "Create New Election")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827; background: transparent;")
        content_layout.addWidget(title)
        content_layout.addSpacing(12)

        # Form fields with labels
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
                border: 2px solid #4B5563;
                background-color: #FFFFFF;
            }
        """

        # Calendar popup styling (keep consistent with the light theme)
        form_style += """
            QCalendarWidget QWidget {
                background: #FFFFFF;
                color: #111827;
            }
            QCalendarWidget QToolButton {
                background: transparent;
                color: #111827;
                font-weight: 600;
                border: none;
                padding: 6px;
            }
            QCalendarWidget QMenu {
                background: #FFFFFF;
                color: #111827;
            }
            QCalendarWidget QSpinBox {
                background: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 2px 6px;
                color: #111827;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #D1FAE5;
                selection-color: #065F46;
                background: #FFFFFF;
                color: #111827;
                outline: none;
            }
        """

        # Ensure combo box popup/list views are white and don't inherit any green tint
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
                background-color: #E5E7EB; /* neutral selection */
                color: #111827;
            }
        """

        label_style = """
            color: #374151;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            margin-bottom: 10px;
        """

        # Title input
        title_label = QLabel("Election Title")
        title_label.setStyleSheet(label_style)
        content_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter election title")
        self.title_input.setStyleSheet(form_style)
        self.title_input.setFixedHeight(48)
        content_layout.addWidget(self.title_input)

        # Date row
        date_row = QHBoxLayout()
        date_row.setSpacing(20)

        # Start date
        start_col = QVBoxLayout()
        start_col.setSpacing(8)
        start_label = QLabel("Start Date")
        start_label.setStyleSheet(label_style)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setMinimumDate(QDate.currentDate())
        self.start_date.setStyleSheet(form_style)
        self.start_date.setFixedHeight(48)
        start_col.addWidget(start_label)
        start_col.addWidget(self.start_date)

        # End date
        end_col = QVBoxLayout()
        end_col.setSpacing(8)
        end_label = QLabel("End Date")
        end_label.setStyleSheet(label_style)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(7))
        self.end_date.setMinimumDate(QDate.currentDate())
        self.end_date.setStyleSheet(form_style)
        self.end_date.setFixedHeight(48)
        end_col.addWidget(end_label)
        end_col.addWidget(self.end_date)

        date_row.addLayout(start_col, 1)
        date_row.addLayout(end_col, 1)
        content_layout.addLayout(date_row)

        # Status
        status_label = QLabel("Status")
        status_label.setStyleSheet(label_style)
        content_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["upcoming", "active", "finalized"])
        self.status_combo.setStyleSheet(form_style)
        self.status_combo.setFixedHeight(48)
        content_layout.addWidget(self.status_combo)
        try:
            self.status_combo.view().setMinimumWidth(320)
        except Exception:
            pass

        # Scope (all/grade/section)
        scope_label = QLabel("Eligible Audience")
        scope_label.setStyleSheet(label_style)
        content_layout.addWidget(scope_label)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["All Students", "Specific Grade", "Specific Section"])
        self.scope_combo.setStyleSheet(form_style + "QComboBox { padding-top: 8px; padding-bottom: 8px; }")
        self.scope_combo.setFixedHeight(48)
        content_layout.addWidget(self.scope_combo)
        try:
            self.scope_combo.view().setMinimumWidth(320)
        except Exception:
            pass

        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(form_style + "QComboBox { padding-top: 8px; padding-bottom: 8px; }")
        self.grade_combo.setFixedHeight(48)
        self.grade_combo.setVisible(False)
        content_layout.addWidget(self.grade_combo)
        try:
            self.grade_combo.view().setMinimumWidth(300)
        except Exception:
            pass

        self.section_combo = QComboBox()
        self.section_combo.setStyleSheet(form_style + "QComboBox { padding-top: 8px; padding-bottom: 8px; }")
        self.section_combo.setFixedHeight(48)
        self.section_combo.setVisible(False)
        content_layout.addWidget(self.section_combo)
        try:
            self.section_combo.view().setMinimumWidth(300)
        except Exception:
            pass

        self.add_section_btn = QPushButton("Add new grade/section")
        self.add_section_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_section_btn.setStyleSheet(
            """
            QPushButton {
                background: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 8px 14px;
                color: #374151;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
            """
        )
        self.add_section_btn.setVisible(False)
        self.add_section_btn.clicked.connect(self._toggle_add_section)
        content_layout.addWidget(self.add_section_btn)

        self.new_grade_input = QLineEdit()
        self.new_grade_input.setPlaceholderText("Enter grade level, e.g., 12")
        self.new_grade_input.setStyleSheet(form_style)
        self.new_grade_input.setFixedHeight(44)
        self.new_grade_input.setVisible(False)
        content_layout.addWidget(self.new_grade_input)

        self.new_section_input = QLineEdit()
        self.new_section_input.setPlaceholderText("Enter section, e.g., STEM-A")
        self.new_section_input.setStyleSheet(form_style)
        self.new_section_input.setFixedHeight(44)
        self.new_section_input.setVisible(False)
        content_layout.addWidget(self.new_section_input)

        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        self.grade_combo.currentIndexChanged.connect(self._on_grade_changed)
        self._populate_grade_options()

        # Add Candidates Section (Collapsible)
        self.candidates_section = QFrame()
        candidates_section_layout = QVBoxLayout(self.candidates_section)
        candidates_section_layout.setContentsMargins(0, 10, 0, 0)
        candidates_section_layout.setSpacing(12)

        # Header with toggle
        # Candidate selection removed: candidates are managed separately and can belong to multiple elections
        note = QLabel("Manage candidates separately. This form now only edits election details.")
        note.setStyleSheet("color: #6B7280; font-size: 12px; background: transparent;")
        note.setWordWrap(True)
        candidates_section_layout.addWidget(note)

        content_layout.addWidget(self.candidates_section)

        # Pre-fill if editing
        if election:
            self.title_input.setText(election.get('title', ''))
            if election.get('start_date'):
                self.start_date.setDate(QDate.fromString(str(election['start_date']), "yyyy-MM-dd"))
            if election.get('end_date'):
                self.end_date.setDate(QDate.fromString(str(election['end_date']), "yyyy-MM-dd"))
            self.status_combo.setCurrentText(election.get('status', 'upcoming'))
            allowed_grade = election.get('allowed_grade')
            allowed_section = election.get('allowed_section')
            self._prefill_scope(allowed_grade, allowed_section)
        else:
            self._on_scope_changed(self.scope_combo.currentIndex())

        # Keep end-date constrained to start-date
        self.start_date.dateChanged.connect(self._sync_end_date_min)
        self._sync_end_date_min(self.start_date.date())

        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)

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

        save_btn = QPushButton("Save Election")
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

    def _sync_end_date_min(self, start: QDate):
        try:
            self.end_date.setMinimumDate(start)
            if self.end_date.date() < start:
                self.end_date.setDate(start)
        except Exception:
            pass

    def accept(self):
        # Validate: start date cannot be in the past
        today = QDate.currentDate()
        start = self.start_date.date()
        end = self.end_date.date()

        if start < today:
            QMessageBox.warning(self, "Invalid Start Date", "Start date cannot be in the past.")
            return
        if end < start:
            QMessageBox.warning(self, "Invalid End Date", "End date cannot be earlier than the start date.")
            return

        super().accept()

    def _toggle_candidates(self):
        """Toggle candidate selection visibility"""
        is_visible = self.candidates_scroll.isVisible()
        self.candidates_scroll.setVisible(not is_visible)

    def _load_candidates(self):
        """Load available candidates into the grid"""
        try:
            all_candidates = list_candidates()

            colors = ["#F59E0B", "#06B6D4", "#8B5CF6", "#3B82F6", "#F59E0B", "#EC4899"]

            row, col = 0, 0
            max_cols = 2

            for idx, candidate in enumerate(all_candidates):
                candidate_item = QFrame()
                candidate_item.setFixedHeight(60)
                candidate_item.setStyleSheet("""
                    QFrame {
                        background: transparent;
                    }
                """)
                
                item_layout = QHBoxLayout(candidate_item)
                item_layout.setContentsMargins(8, 8, 8, 8)
                item_layout.setSpacing(12)
                
                # Checkbox (visible, styled for click target)
                checkbox = QCheckBox()
                checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                checkbox.setProperty("candidate_id", candidate.get('candidate_id'))
                checkbox.setStyleSheet("""
                    QCheckBox::indicator {
                        width: 18px; height: 18px;
                        border: 2px solid #10B981;
                        border-radius: 4px;
                        background: #FFFFFF;
                    }
                    QCheckBox::indicator:checked {
                        background: #10B981;
                        image: none;
                    }
                """)
                checkbox.toggled.connect(lambda checked, cid=candidate.get('candidate_id'): self._on_candidate_selected(cid, checked))
                self._candidate_checkboxes.append((candidate.get('candidate_id'), checkbox))
                
                # Avatar circle
                avatar = QLabel()
                avatar.setFixedSize(44, 44)
                color = colors[idx % len(colors)]
                avatar.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color};
                        border-radius: 22px;
                    }}
                """)
                
                # Candidate info
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)
                
                name_lbl = QLabel(candidate.get('full_name', 'Unknown'))
                name_lbl.setFont(QFont("Segoe UI", 12))
                name_lbl.setStyleSheet("color: #111827;")
                
                position_lbl = QLabel(candidate.get('position', 'President'))
                position_lbl.setFont(QFont("Segoe UI", 10))
                position_lbl.setStyleSheet("color: #6B7280;")
                
                info_layout.addWidget(name_lbl)
                info_layout.addWidget(position_lbl)
                
                item_layout.addWidget(checkbox)
                item_layout.addWidget(avatar)
                item_layout.addLayout(info_layout, 1)

                # Make entire row clickable to toggle checkbox
                def _toggle_checked(event, cb=checkbox):
                    cb.setChecked(not cb.isChecked())
                candidate_item.mousePressEvent = _toggle_checked
                
                # Pre-select if editing and candidate already belongs to this election
                if self.election and candidate.get('election_id') == self.election.get('election_id'):
                    checkbox.setChecked(True)
                    self._on_candidate_selected(candidate.get('candidate_id'), True)

                self.candidates_grid.addWidget(candidate_item, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        except Exception as e:
            print(f"Error loading candidates: {e}")

    def _on_candidate_selected(self, candidate_id: int, checked: bool):
        """Track selected candidates"""
        if checked and candidate_id not in self.selected_candidates:
            self.selected_candidates.append(candidate_id)
        elif not checked and candidate_id in self.selected_candidates:
            self.selected_candidates.remove(candidate_id)

    def _on_scope_changed(self, index: int):
        scope = self.scope_combo.currentText()
        show_grade = scope in ("Specific Grade", "Specific Section")
        show_section = scope == "Specific Section"

        if not show_grade:
            self._reset_add_section_mode()

        self.grade_combo.setVisible(show_grade)
        self.section_combo.setVisible(show_section and not self.adding_new_section)
        self.add_section_btn.setVisible(show_grade)

        if not show_grade:
            self.grade_combo.setCurrentIndex(0)
        if not show_section:
            self.section_combo.setCurrentIndex(0)

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
        if self.adding_new_section:
            return
        grade_level = self.grade_combo.currentData()
        self._populate_section_options(grade_level)

    def _toggle_add_section(self):
        self.adding_new_section = not self.adding_new_section
        self.new_grade_input.setVisible(self.adding_new_section)
        self.new_section_input.setVisible(self.adding_new_section)
        self.grade_combo.setEnabled(not self.adding_new_section)
        self.section_combo.setEnabled(not self.adding_new_section)
        self.section_combo.setVisible(not self.adding_new_section and self.scope_combo.currentText() == "Specific Section")
        self.add_section_btn.setText("Cancel new section" if self.adding_new_section else "Add new grade/section")

    def _reset_add_section_mode(self):
        self.adding_new_section = False
        self.new_grade_input.setVisible(False)
        self.new_section_input.setVisible(False)
        self.grade_combo.setEnabled(True)
        self.section_combo.setEnabled(True)
        self.section_combo.setVisible(self.scope_combo.currentText() == "Specific Section")
        self.add_section_btn.setText("Add new grade/section")

    def _prefill_scope(self, allowed_grade, allowed_section):
        if allowed_grade is None and not allowed_section:
            self.scope_combo.setCurrentText("All Students")
            self._on_scope_changed(self.scope_combo.currentIndex())
            return

        target_scope = "Specific Section" if allowed_section else "Specific Grade"
        self.scope_combo.setCurrentText(target_scope)

        if allowed_grade is not None and not any(s.get('grade_level') == allowed_grade for s in self.sections):
            self.sections.append({'grade_level': allowed_grade, 'section_name': allowed_section or ''})
            self._populate_grade_options()

        if allowed_grade is not None:
            idx = self.grade_combo.findData(allowed_grade)
            if idx != -1:
                self.grade_combo.setCurrentIndex(idx)
                self._populate_section_options(allowed_grade)

        if allowed_section:
            sidx = self.section_combo.findData(allowed_section)
            if sidx != -1:
                self.section_combo.setCurrentIndex(sidx)

        self._on_scope_changed(self.scope_combo.currentIndex())

    def get_data(self) -> dict:
        scope = self.scope_combo.currentText()
        allowed_grade = None
        allowed_section = None
        new_section = None

        if scope == "Specific Grade":
            if self.adding_new_section:
                allowed_grade = self.new_grade_input.text().strip() or None
                allowed_section = self.new_section_input.text().strip() or None
                if allowed_grade and allowed_section:
                    new_section = {"grade_level": allowed_grade, "section_name": allowed_section}
            else:
                allowed_grade = self.grade_combo.currentData()
        elif scope == "Specific Section":
            if self.adding_new_section:
                allowed_grade = self.new_grade_input.text().strip() or None
                allowed_section = self.new_section_input.text().strip() or None
                if allowed_grade and allowed_section:
                    new_section = {"grade_level": allowed_grade, "section_name": allowed_section}
            else:
                allowed_grade = self.grade_combo.currentData()
                allowed_section = self.section_combo.currentData()

        return {
            'title': self.title_input.text().strip(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'status': self.status_combo.currentText(),
            'allowed_grade': allowed_grade,
            'allowed_section': allowed_section,
            'new_section': new_section,
        }


class ManageElectionsPage(QWidget):
    """Page for managing elections"""

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
        self.table = DataTable(["Title", "Start Date", "End Date", "Status", "Candidates", "Actions"])
        card_layout.addWidget(self.table, 1)

        layout.addWidget(card)

    def _load_data(self):
        """Load elections from database"""
        try:
            self._elections = list_elections()
            self._filter_elections()
        except Exception as e:
            print(f"Load elections error: {e}")

    def _filter_elections(self):
        """Filter elections based on search text"""
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
            status = election.get('status')

            # If status is missing/empty, infer from dates
            if not status:
                today = QDate.currentDate()
                s_date = election.get('start_date')
                e_date = election.get('end_date')

                # Convert to QDate if they are strings/objects
                if s_date and not isinstance(s_date, QDate):
                    s_date = QDate.fromString(str(s_date)[:10], "yyyy-MM-dd")
                if e_date and not isinstance(e_date, QDate):
                    e_date = QDate.fromString(str(e_date)[:10], "yyyy-MM-dd")

                if e_date and today > e_date:
                    status = "finalized"
                elif s_date and today < s_date:
                    status = "upcoming"
                elif s_date and e_date:
                    status = "active"
                else:
                    status = "unknown"

            badge = StatusBadge(status)
            self.table.setCellWidget(row, 3, badge)

            # Candidates count
            count = election.get('candidate_count', 0)
            candidates_widget = QLabel(f"👥 {count} candidates")
            candidates_widget.setFont(QFont("Segoe UI", 10))
            candidates_widget.setStyleSheet("color: #10B981;")
            self.table.setCellWidget(row, 4, candidates_widget)

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

        self.table.setRowHeight(0, 55)
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 55)

    def _create_election(self):
        dialog = ElectionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            new_section = data.pop('new_section', None)
            if new_section:
                try:
                    grade_val = int(new_section.get('grade_level'))
                except Exception:
                    QMessageBox.warning(self, "Error", "Grade level must be a number when adding a new section.")
                    return
                ok, msg = add_new_section(grade_val, new_section.get('section_name'))
                if not ok:
                    QMessageBox.warning(self, "Error", msg)
                    return
                data['allowed_grade'] = grade_val
                data['allowed_section'] = new_section.get('section_name')
            if not data['title']:
                QMessageBox.warning(self, "Error", "Title is required")
                return

            ok, msg = create_election(data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def _edit_election(self, election_id: int):
        election = next((e for e in self._elections if e['election_id'] == election_id), None)
        if not election:
            return

        dialog = ElectionDialog(self, election)
        if dialog.exec():
            data = dialog.get_data()
            new_section = data.pop('new_section', None)
            if new_section:
                try:
                    grade_val = int(new_section.get('grade_level'))
                except Exception:
                    QMessageBox.warning(self, "Error", "Grade level must be a number when adding a new section.")
                    return
                ok, msg = add_new_section(grade_val, new_section.get('section_name'))
                if not ok:
                    QMessageBox.warning(self, "Error", msg)
                    return
                data['allowed_grade'] = grade_val
                data['allowed_section'] = new_section.get('section_name')
            ok, msg = update_election(election_id, data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def _toggle_status(self, election_id: int, current_status: str):
        # Toggle between active and upcoming; finalized stays as is
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
        self._load_data()

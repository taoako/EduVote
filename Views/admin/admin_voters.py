"""
Manage Voters Page - View and manage registered voters
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QTableWidgetItem, QDialog,
    QLineEdit, QMessageBox, QPushButton, QComboBox, QScrollArea
)
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCore import Qt

from .admin_components import GreenButton, SearchBar, DataTable, StatusBadge, ActionButton, StatCard
from Models.validators import is_valid_optional_email
from Controller.controller_voters import (
    list_voters_with_status,
    create_voter,
    update_voter,
    delete_voter,
    voter_stats,
    list_sections,
    add_section,
)


class VoterDialog(QDialog):
    """Dialog for adding/editing a voter"""

    def __init__(self, parent=None, voter: dict = None):
        super().__init__(parent)
        self.voter = voter
        self.sections = list_sections() or []
        self.adding_new_section = False
        self.setWindowTitle("Edit Voter" if voter else "Add Voter")
        self.setFixedSize(600, 620)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(32, 28, 32, 36)
        outer_layout.setSpacing(16)

        title = QLabel("Edit Voter" if voter else "Add New Voter")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827; background: transparent;")
        outer_layout.addWidget(title)
        outer_layout.addSpacing(12)

        form_style = """
            QLineEdit, QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #111827;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4B5563;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; width: 0; height: 0; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                color: #111827;
                outline: none;
                selection-background-color: #E5E7EB;
                selection-color: #111827;
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
            margin-bottom: 12px;
        """

        # Scrollable content (form)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Full Name
        name_label = QLabel("Full Name")
        name_label.setStyleSheet(label_style)
        content_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter voter's full name")
        self.name_input.setStyleSheet(form_style)
        self.name_input.setFixedHeight(48)
        content_layout.addWidget(self.name_input)

        # Student ID
        sid_label = QLabel("Student ID")
        sid_label.setStyleSheet(label_style)
        content_layout.addWidget(sid_label)

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("e.g., STU-001")
        self.student_id_input.setStyleSheet(form_style)
        self.student_id_input.setFixedHeight(48)
        content_layout.addWidget(self.student_id_input)

        # Grade Level
        grade_label = QLabel("Grade Level")
        grade_label.setStyleSheet(label_style)
        content_layout.addWidget(grade_label)

        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(form_style + "QComboBox { padding-top: 8px; padding-bottom: 8px; }")
        self.grade_combo.setFixedHeight(48)
        content_layout.addWidget(self.grade_combo)
        self.grade_combo.currentIndexChanged.connect(self._on_grade_changed)
        try:
            self.grade_combo.view().setMinimumWidth(300)
        except Exception:
            pass

        # Section
        section_label = QLabel("Section")
        section_label.setStyleSheet(label_style)
        content_layout.addWidget(section_label)

        self.section_combo = QComboBox()
        self.section_combo.setStyleSheet(form_style + "QComboBox { padding-top: 10px; padding-bottom: 10px; }")
        self.section_combo.setFixedHeight(50)
        content_layout.addWidget(self.section_combo)
        try:
            self.section_combo.view().setMinimumWidth(300)
        except Exception:
            pass

        content_layout.addSpacing(12)

        self.add_section_btn = QPushButton("Add new grade/section")
        self.add_section_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_section_btn.setStyleSheet(
            """
            QPushButton {
                background: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 8px 14px;
                color: #374151;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
            """
        )
        self.add_section_btn.setFixedHeight(36)
        self.add_section_btn.clicked.connect(self._toggle_add_section)
        content_layout.addWidget(self.add_section_btn)

        self.new_grade_input = QLineEdit()
        self.new_grade_input.setPlaceholderText("Enter grade level, e.g., 12")
        self.new_grade_input.setStyleSheet(form_style)
        self.new_grade_input.setFixedHeight(46)
        self.new_grade_input.setVisible(False)
        content_layout.addWidget(self.new_grade_input)

        self.new_section_input = QLineEdit()
        self.new_section_input.setPlaceholderText("Enter section, e.g., STEM-A")
        self.new_section_input.setStyleSheet(form_style)
        self.new_section_input.setFixedHeight(46)
        self.new_section_input.setVisible(False)
        content_layout.addWidget(self.new_section_input)

        # Email
        email_label = QLabel("Email Address")
        email_label.setStyleSheet(label_style)
        content_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setStyleSheet(form_style)
        self.email_input.setFixedHeight(48)
        content_layout.addWidget(self.email_input)

        # Password (only for new voters)
        pwd_label = QLabel("Password" if not voter else "New Password (optional)")
        pwd_label.setStyleSheet(label_style)
        content_layout.addWidget(pwd_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password" if not voter else "Leave blank to keep current")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(form_style)
        self.password_input.setFixedHeight(48)
        content_layout.addWidget(self.password_input)

        # Populate dropdowns
        self._populate_grade_options()
        self._on_grade_changed(self.grade_combo.currentIndex())

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll, 1)

        # Pre-fill if editing
        if voter:
            self.name_input.setText(voter.get('full_name', ''))
            self.student_id_input.setText(voter.get('student_id', ''))
            self.email_input.setText(voter.get('email', ''))
            self._prefill_grade_section(voter.get('grade_level'), voter.get('section'))

        content_layout.addStretch()

        # add scroll area to outer layout done above

        # Inline validation warning
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: 600;")
        self.warning_label.setVisible(False)
        outer_layout.addWidget(self.warning_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(46)
        cancel_btn.setMinimumWidth(130)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFont(QFont("Segoe UI", 13))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F3F4F6;
                border: 2px solid #E5E7EB;
                border-radius: 22px;
                padding: 10px 26px;
                color: #6B7280;
                font-weight: 600;
            }
            QPushButton:hover { 
                background: #E5E7EB;
                color: #374151;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save Voter")
        self.save_btn.setFixedHeight(46)
        self.save_btn.setMinimumWidth(150)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 26px;
            }
            QPushButton:hover { 
                background-color: #059669;
            }
        """)
        self.save_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.save_btn)
        outer_layout.addLayout(btn_row)

        # Live validation
        self.name_input.textChanged.connect(self._validate_form)
        self.student_id_input.textChanged.connect(self._validate_form)
        self.email_input.textChanged.connect(self._validate_form)
        self.password_input.textChanged.connect(self._validate_form)
        self.grade_combo.currentIndexChanged.connect(self._validate_form)
        self.section_combo.currentIndexChanged.connect(self._validate_form)
        self.new_grade_input.textChanged.connect(self._validate_form)
        self.new_section_input.textChanged.connect(self._validate_form)
        self._validate_form()

    def get_data(self) -> dict:
        grade_level = None
        section = None
        new_section = None

        if self.adding_new_section:
            grade_level = self.new_grade_input.text().strip() or None
            section = self.new_section_input.text().strip() or None
            if grade_level and section:
                new_section = {"grade_level": grade_level, "section_name": section}
        else:
            grade_level = self.grade_combo.currentData()
            section = self.section_combo.currentData()

        return {
            'full_name': self.name_input.text().strip(),
            'student_id': self.student_id_input.text().strip(),
            'email': self.email_input.text().strip(),
            'password': self.password_input.text(),
            'grade_level': grade_level,
            'section': section,
            'new_section': new_section,
        }

    def accept(self):
        if not self._validate_form():
            return
        super().accept()

    def _validate_form(self) -> bool:
        message = None
        name = self.name_input.text().strip()
        student_id = self.student_id_input.text().strip()
        email = (self.email_input.text() or "").strip()
        password = self.password_input.text() if not self.voter else self.password_input.text()

        if not name:
            message = "Full name is required."
        elif not student_id:
            message = "Student ID is required."
        elif not email:
            message = "Email is required."
        elif not is_valid_optional_email(email):
            message = "Please enter a valid email address (example: name@school.com)."
        elif not self.voter and not password:
            message = "Password is required for new voters."

        if message is None:
            if self.adding_new_section:
                grade_val = (self.new_grade_input.text() or "").strip()
                section_val = (self.new_section_input.text() or "").strip()
                if not grade_val or not section_val:
                    message = "Grade level and section are required."
                else:
                    try:
                        int(grade_val)
                    except Exception:
                        message = "Grade level must be a number."
            else:
                if self.grade_combo.currentData() is None:
                    message = "Select a grade level."
                elif self.section_combo.currentData() is None:
                    message = "Select a section."

        self.warning_label.setVisible(bool(message))
        if message:
            self.warning_label.setText(f"⚠ {message}")
        self.save_btn.setEnabled(message is None)
        return message is None

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
        self.add_section_btn.setText("Cancel new section" if self.adding_new_section else "Add new grade/section")
        self._validate_form()

    def _prefill_grade_section(self, grade_level, section_name):
        if grade_level is not None and not any(s.get('grade_level') == grade_level for s in self.sections):
            self.sections.append({'grade_level': grade_level, 'section_name': section_name or ''})
            self._populate_grade_options()

        if grade_level is not None:
            idx = self.grade_combo.findData(grade_level)
            if idx != -1:
                self.grade_combo.setCurrentIndex(idx)
                self._populate_section_options(grade_level)

        if section_name:
            sidx = self.section_combo.findData(section_name)
            if sidx != -1:
                self.section_combo.setCurrentIndex(sidx)


class ManageVotersPage(QWidget):
    """Page for managing voters/students"""

    def __init__(self):
        super().__init__()
        self._voters = []
        self._search_text = ""
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Search and Add row
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        self.search_bar = SearchBar("Search by name or student ID...")
        self.search_bar.setMinimumWidth(400)
        self.search_bar.textChanged.connect(self._on_search)

        add_btn = GreenButton("Add Voter")
        add_btn.clicked.connect(self._add_voter)

        top_row.addWidget(self.search_bar)
        top_row.addStretch()
        top_row.addWidget(add_btn)
        layout.addLayout(top_row)

        # Stats cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        self.total_card = StatCard("Total Voters", "0", "👥", dark=True)
        self.voted_card = StatCard("Voted", "0", "☑", dark=True)
        self.not_voted_card = StatCard("Not Voted", "0", "⚠", dark=True)

        stats_row.addWidget(self.total_card)
        stats_row.addWidget(self.voted_card)
        stats_row.addWidget(self.not_voted_card)
        layout.addLayout(stats_row)

        # Main table card
        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 20px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)

        self.table = DataTable(["Student ID", "Name", "Grade", "Section", "Email", "Status", "Voted At", "Actions"])
        card_layout.addWidget(self.table)

        layout.addWidget(card, 1)

    def _load_data(self):
        """Load voters from database"""
        try:
            self._voters = list_voters_with_status()
            self._update_stats()
            self._populate_table()
        except Exception as e:
            print(f"Load voters error: {e}")

    def _update_stats(self):
        total = len(self._voters)
        voted = sum(1 for v in self._voters if v.get('voted_at'))
        not_voted = total - voted

        self.total_card.set_value(str(total))
        self.voted_card.set_value(str(voted))
        self.not_voted_card.set_value(str(not_voted))

    def _populate_table(self):
        # Filter by search
        filtered = self._voters
        if self._search_text:
            search = self._search_text.lower()
            filtered = [v for v in self._voters
                        if search in v.get('full_name', '').lower()
                        or search in v.get('student_id', '').lower()]

        self.table.setRowCount(len(filtered))

        for row, voter in enumerate(filtered):
            # Student ID
            self.table.setItem(row, 0, QTableWidgetItem(voter.get('student_id', '')))

            # Name
            self.table.setItem(row, 1, QTableWidgetItem(voter.get('full_name', '')))

            # Email
            grade_val = voter.get('grade_level')
            grade_text = str(grade_val) if grade_val is not None else "—"
            self.table.setItem(row, 2, QTableWidgetItem(grade_text))

            self.table.setItem(row, 3, QTableWidgetItem(voter.get('section', '') or "—"))

            self.table.setItem(row, 4, QTableWidgetItem(voter.get('email', '')))

            # Status
            voted_at = voter.get('voted_at')
            status = "voted" if voted_at else "not_voted"
            badge = StatusBadge(status)
            self.table.setCellWidget(row, 5, badge)

            # Voted At
            voted_str = str(voted_at)[:19] if voted_at else "—"
            self.table.setItem(row, 6, QTableWidgetItem(voted_str))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(8)

            edit_btn = ActionButton("edit")
            delete_btn = ActionButton("delete")

            user_id = voter.get('user_id')
            edit_btn.clicked.connect(lambda checked, uid=user_id: self._edit_voter(uid))
            delete_btn.clicked.connect(lambda checked, uid=user_id: self._delete_voter(uid))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 7, actions_widget)
            self.table.setRowHeight(row, 55)

    def _on_search(self, text: str):
        self._search_text = text
        self._populate_table()

    def _add_voter(self):
        dialog = VoterDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            new_section = data.pop('new_section', None)
            if new_section:
                try:
                    grade_val = int(new_section.get('grade_level'))
                except Exception:
                    return
                ok, msg = add_section(grade_val, new_section.get('section_name'))
                if not ok:
                    QMessageBox.warning(self, "Error", msg)
                    return
                data['grade_level'] = grade_val
                data['section'] = new_section.get('section_name')
            if not data['full_name'] or not data['email'] or not data['password']:
                return
            success, msg = create_voter(data)
            if success:
                self._load_data()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _edit_voter(self, user_id: int):
        voter = next((v for v in self._voters if v['user_id'] == user_id), None)
        if not voter:
            return

        dialog = VoterDialog(self, voter)
        if dialog.exec():
            data = dialog.get_data()
            new_section = data.pop('new_section', None)
            if new_section:
                try:
                    grade_val = int(new_section.get('grade_level'))
                except Exception:
                    return
                ok, msg = add_section(grade_val, new_section.get('section_name'))
                if not ok:
                    QMessageBox.warning(self, "Error", msg)
                    return
                data['grade_level'] = grade_val
                data['section'] = new_section.get('section_name')
            ok, msg = update_voter(user_id, data)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def _delete_voter(self, user_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this voter?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = delete_voter(user_id)
            if not ok:
                QMessageBox.warning(self, "Error", msg)
            else:
                self._load_data()

    def refresh(self):
        self._load_data()

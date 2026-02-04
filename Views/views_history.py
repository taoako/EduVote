from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QTableWidget, \
    QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from Views.components import CircularAvatar


class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 30px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Voting Activity Log")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a1a1a; margin-bottom: 20px;")
        card_layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Election Event", "Voted For", "Status"])
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setFrameShape(QFrame.Shape.NoFrame)
        table.setStyleSheet("""
            QTableWidget { background: transparent; selection-background-color: transparent; }
            QHeaderView::section { 
                background: white; color: #6B7280; font-weight: bold; border: none; 
                border-bottom: 1px solid #E5E7EB; padding: 10px; text-align: left;
            }
            QTableWidget::item { border-bottom: 1px solid #F3F4F6; padding: 15px; color: #374151; }
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        table.setRowCount(0)
        self.table = table
        card_layout.addWidget(table)
        layout.addWidget(card)

    def set_history(self, rows):
        self.rows = rows or []

        if not self.rows:
            self.table.clearContents()
            try:
                self.table.clearSpans()
            except Exception:
                pass
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 4)
            msg = QTableWidgetItem("No voting activity yet.")
            msg.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setForeground(QColor("#6B7280"))
            self.table.setItem(0, 0, msg)
            self.table.setRowHeight(0, 60)
            return

        try:
            self.table.clearSpans()
        except Exception:
            pass
        self.table.setRowCount(len(self.rows))

        for row_idx, entry in enumerate(self.rows):
            date = entry.get("voted_at", "-")
            election_title = entry.get("election_title", "-")
            raw_status = (entry.get("status", "cast") or "cast")
            status_key = str(raw_status).lower()

            if status_key == "spoiled":
                status = "Abstained"
                candidate_name = "Abstained"
                voted_text = "User abstained from voting"
            else:
                status = "Casted" if status_key == "cast" else str(raw_status).capitalize()
                candidate_name = entry.get("candidate_name") or "Abstained"
                voted_text = f"Voted for: {candidate_name}"

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(date)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(election_title)))

            cell_widget = QWidget()
            l = QHBoxLayout(cell_widget)
            l.setContentsMargins(4, 6, 4, 6)
            l.setSpacing(10)
            l.addWidget(CircularAvatar("#10B981", str(candidate_name)[0], 30))
            voted_lbl = QLabel(voted_text)
            voted_lbl.setStyleSheet("color: #111827; font-weight: 600;")
            l.addWidget(voted_lbl)
            l.addStretch()
            self.table.setCellWidget(row_idx, 2, cell_widget)

            badge = QLabel(f" {status} " + ("✅" if status.lower() == "casted" else ""))
            badge.setFixedHeight(28)
            badge.setMinimumWidth(110)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Render as a subtle badge (not button-like)
            is_cast = status.lower() == "casted"
            fg = "#059669" if is_cast else "#6B7280"
            border = "#A7F3D0" if is_cast else "#E5E7EB"
            badge.setStyleSheet(
                "QLabel {"
                f"color: {fg};"
                f"border: 1px solid {border};"
                "background: transparent;"
                "border-radius: 10px;"
                "font-weight: 700;"
                "padding: 2px 10px;"
                "}"
            )

            cont = QWidget()
            cl = QHBoxLayout(cont)
            cl.setContentsMargins(0, 0, 8, 0)
            cl.addWidget(badge)
            cl.addStretch()
            self.table.setCellWidget(row_idx, 3, cont)
            self.table.setRowHeight(row_idx, 78)
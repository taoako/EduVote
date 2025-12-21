"""
Admin Components Module - Reusable UI components for the Admin Panel
Following OOP principles with inheritance and composition
"""
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect, QLineEdit, QTableWidget, QHeaderView
)
from PyQt6.QtGui import QFont, QColor, QCursor, QPainter, QPen, QBrush, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRectF, QSize
import math


class AdminSidebarButton(QPushButton):
    """Sidebar navigation button for admin panel - pill style with icon"""

    def __init__(self, text: str, icon_label: str = ""):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(50)
        self.setCheckable(False)

        self._icon = icon_label
        self._text = text
        self._update_display()

        self._base_style = """
            QPushButton {
                text-align: left;
                padding: 0 18px;
                border-radius: 25px;
                border: none;
                background: transparent;
                color: #374151;
                font-size: 13px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #F0FDF4;
            }
        """
        self._active_style = """
            QPushButton {
                text-align: left;
                padding: 0 18px;
                border-radius: 25px;
                border: none;
                background: #10B981;
                color: white;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }
        """
        self.setStyleSheet(self._base_style)

    def _update_display(self):
        self.setText(f"{self._icon}   {self._text}" if self._icon else self._text)

    def set_active(self, active: bool):
        self.setStyleSheet(self._active_style if active else self._base_style)


class StatCard(QFrame):
    """Statistics card widget displaying a metric with icon"""

    def __init__(self, title: str, value: str, icon: str = "👥", dark: bool = True):
        super().__init__()
        self.setFixedHeight(140)
        self.setMinimumWidth(240)

        # Keep StatCards consistent with the project's light theme
        bg_color = "#FFFFFF"
        title_color = "#6B7280"
        value_color = "#111827"
        border = "border: 1px solid #E5E7EB;"

        # Use a small accent strip so cards are visually distinct without dark backgrounds
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {bg_color};
                border-radius: 20px;
                {border}
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        # Top row - title and icon
        top_row = QHBoxLayout()
        top_row.setSpacing(0)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 12))
        title_lbl.setStyleSheet(f"color: {title_color}; background: transparent;")

        # Icon in a subtle green chip (consistent with the rest of the app)
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 18))
        icon_lbl.setFixedSize(38, 38)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            "background-color: #ECFDF5; color: #10B981; border-radius: 19px;"
        )

        top_row.addWidget(title_lbl, 1)
        top_row.addWidget(icon_lbl)
        layout.addLayout(top_row)

        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(f"color: {value_color}; background: transparent;")
        layout.addWidget(self.value_lbl)

    def set_value(self, value: str):
        self.value_lbl.setText(value)


class StatusBadge(QLabel):
    """Status badge widget with colored background"""

    STYLES = {
        "active": ("#D1FAE5", "#10B981"),
        "upcoming": ("#DBEAFE", "#3B82F6"),
        "finalized": ("#FEE2E2", "#EF4444"),
        "ended": ("#FEE2E2", "#EF4444"),
        "voted": ("#D1FAE5", "#10B981"),
        "not_voted": ("#FEE2E2", "#EF4444"),
    }

    def __init__(self, status: str):
        super().__init__()
        self._set_status(status)

    def _set_status(self, status: str):
        status_key = (str(status) if status is not None else "").strip().lower()
        status_key = status_key.replace(" ", "_").replace("-", "_")
        if not status_key:
            status_key = "unknown"

        bg, fg = self.STYLES.get(status_key, ("#E5E7EB", "#6B7280"))
        display_text = status_key.replace("_", " ").title()

        # Ensure the badge always shows text
        if not display_text.strip():
            display_text = "Unknown"

        self.setText(display_text)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(70)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 14px;
                padding: 4px 12px;
            }}
        """)

    def set_status(self, status: str):
        self._set_status(status)


class ActionButton(QPushButton):
    """Action button with icon for tables"""

    STYLES = {
        # fg (primary), hover/bg, glyph text for icon generation
        "edit": ("#3B82F6", "#DBEAFE", "E"),
        "delete": ("#EF4444", "#FEE2E2", "X"),
        "pause": ("#F59E0B", "#FEF3C7", "II"),
        "play": ("#10B981", "#D1FAE5", "▶"),
        "view": ("#6366F1", "#E0E7FF", "V"),
        "finalize": ("#EF4444", "#FEE2E2", "■"),
    }

    def __init__(self, action_type: str, text: str = ""):
        super().__init__()
        fg, bg, glyph = self.STYLES.get(action_type, ("#6B7280", "#F3F4F6", "•"))

        # Build a small round icon with a letter/shape so we don't rely on emoji
        icon = self._build_icon(glyph, fg)
        self.setIcon(icon)
        self.setIconSize(QSize(18, 18))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(QFont("Segoe UI", 10))

        display = f" {text}" if text else ""
        self.setText(display)

        if text:
            self.setFixedHeight(36)
            self.setMinimumWidth(80)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {fg};
                    border: 1px solid {fg};
                    border-radius: 18px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {fg};
                    color: white;
                }}
            """)
        else:
            self.setFixedSize(32, 32)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {fg};
                    border: none;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {bg};
                    border-radius: 16px;
                }}
            """)

    def _build_icon(self, glyph: str, color: str) -> QIcon:
        pix = QPixmap(20, 20)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 20, 20)
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
        painter.end()
        return QIcon(pix)


class SearchBar(QLineEdit):
    """Search input with icon"""

    def __init__(self, placeholder: str = "Search..."):
        super().__init__()
        self.setPlaceholderText(f"🔍  {placeholder}")
        self.setFixedHeight(45)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 22px;
                padding: 10px 20px;
                color: #374151;
            }
            QLineEdit:focus {
                border: 2px solid #10B981;
            }
        """)


class DataTable(QTableWidget):
    """Styled data table for admin panels"""

    def __init__(self, headers: list[str]):
        super().__init__()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                border-radius: 12px;
                color: #111827;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F3F4F6;
                color: #111827;
            }
            QTableWidget::item:alternate {
                background-color: #FAFAFA;
            }
            QTableWidget::item:selected {
                background-color: #E5E7EB;
                color: #111827;
            }
            QHeaderView::section {
                background-color: #FFFFFF;
                color: #10B981;
                font-weight: bold;
                font-size: 12px;
                padding: 14px 8px;
                border: none;
                border-bottom: 2px solid #E5E7EB;
            }
        """)


class BarChart(QWidget):
    """Simple bar chart widget"""

    def __init__(self, data: list[tuple[str, int]] = None):
        super().__init__()
        self._data = data or []
        self.setMinimumHeight(250)

    def set_data(self, data: list[tuple[str, int]]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin_left, margin_bottom = 50, 60
        chart_w = w - margin_left - 20
        chart_h = h - margin_bottom - 30

        max_val = max(v for _, v in self._data) or 1
        bar_width = min(60, chart_w // len(self._data) - 20)

        # Draw Y-axis labels
        painter.setPen(QPen(QColor("#9CA3AF")))
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(5):
            y = 20 + chart_h - (chart_h * i / 4)
            val = int(max_val * i / 4)
            painter.drawText(0, int(y) - 5, margin_left - 10, 20, Qt.AlignmentFlag.AlignRight, str(val))
            painter.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DotLine))
            painter.drawLine(margin_left, int(y), w - 20, int(y))
            painter.setPen(QPen(QColor("#9CA3AF")))

        # Draw bars
        for i, (label, value) in enumerate(self._data):
            x = margin_left + 20 + i * (chart_w // len(self._data))
            bar_h = (value / max_val) * chart_h
            y = 20 + chart_h - bar_h

            # Bar gradient
            painter.setBrush(QBrush(QColor("#10B981")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_width, bar_h), 6, 6)

            # Label
            painter.setPen(QPen(QColor("#6B7280")))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(int(x) - 10, h - margin_bottom + 10, bar_width + 20, 40,
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, label)


class PieChart(QWidget):
    """Simple pie chart widget with hover effects and bottom legend"""

    COLORS = ["#10B981", "#3B82F6", "#8B5CF6", "#06B6D4", "#F59E0B", "#EF4444"]

    def __init__(self, data: list[tuple[str, int]] = None):
        super().__init__()
        self._data = data or []
        self.setMinimumSize(300, 450)
        self.setMouseTracking(True)
        self._hovered_index = -1
        self._pie_rect = QRectF()

    def set_data(self, data: list[tuple[str, int]]):
        self._data = data
        self.update()

    def mouseMoveEvent(self, event):
        if not self._data:
            return

        pos = event.position()
        center = self._pie_rect.center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        dist = math.sqrt(dx*dx + dy*dy)

        # Check if inside pie circle
        if dist > self._pie_rect.width() / 2:
            if self._hovered_index != -1:
                self._hovered_index = -1
                self.update()
            return

        # Calculate angle from 12 o'clock (clockwise)
        # 12 o'clock vector is (0, -1)
        # atan2(dx, -dy) gives angle from Y-axis (up)
        angle = math.degrees(math.atan2(dx, -dy))
        if angle < 0:
            angle += 360

        # Find which slice covers this angle
        total = sum(v for _, v in self._data) or 1
        current_angle = 0
        found = -1
        for i, (_, value) in enumerate(self._data):
            span = (value / total) * 360
            if current_angle <= angle < current_angle + span:
                found = i
                break
            current_angle += span

        if self._hovered_index != found:
            self._hovered_index = found
            self.update()

    def leaveEvent(self, event):
        self._hovered_index = -1
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Layout: Pie on top, Legend at bottom
        # Reserve space for legend at bottom
        legend_height = 100
        pie_size = min(w, h - legend_height) - 20
        if pie_size < 100: pie_size = 100

        pie_x = (w - pie_size) / 2
        pie_y = 10
        self._pie_rect = QRectF(pie_x, pie_y, pie_size, pie_size)

        total = sum(v for _, v in self._data) or 1
        start_angle = 90 * 16 # 12 o'clock in Qt angles (1/16th degree)

        # Draw Pie Slices
        for i, (label, value) in enumerate(self._data):
            span = int((value / total) * 360 * 16)
            color = QColor(self.COLORS[i % len(self.COLORS)])

            if i == self._hovered_index:
                painter.setBrush(QBrush(color.lighter(110)))
                # Optional: Draw slightly larger slice or offset it
            else:
                painter.setBrush(QBrush(color))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(self._pie_rect, start_angle, -span)
            start_angle -= span

        # Draw Center Info if Hovered
        if self._hovered_index != -1:
            label, value = self._data[self._hovered_index]
            pct = (value / total) * 100

            # Draw a semi-transparent overlay in center
            center_rect = QRectF(0, 0, pie_size/2, pie_size/2)
            center_rect.moveCenter(self._pie_rect.center())

            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawEllipse(center_rect)

            painter.setPen(QPen(QColor("#111827")))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(center_rect, Qt.AlignmentFlag.AlignCenter, f"{label}\n{value} ({pct:.1f}%)")

        # Draw Legend at Bottom (Flow Layout)
        legend_y = pie_y + pie_size + 20
        x_cursor = 20
        y_cursor = legend_y
        row_height = 25

        painter.setFont(QFont("Segoe UI", 9))

        for i, (label, value) in enumerate(self._data):
            color = QColor(self.COLORS[i % len(self.COLORS)])
            pct = f"{value / total * 100:.0f}%"
            text = f"{label} ({pct})"

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(text)
            item_w = 20 + text_w + 20 # dot + text + padding

            # Wrap to next line if needed
            if x_cursor + item_w > w:
                x_cursor = 20
                y_cursor += row_height

            # Draw dot
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x_cursor), int(y_cursor), 10, 10)

            # Draw text
            painter.setPen(QPen(QColor("#374151")))
            painter.drawText(int(x_cursor) + 16, int(y_cursor) + 9, text)

            x_cursor += item_w


class GreenButton(QPushButton):
    """Green action button with + icon"""

    def __init__(self, text: str):
        super().__init__(f"+  {text}")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(45)
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)


class WinnerBanner(QFrame):
    """Winner announcement banner with trophy"""

    def __init__(self, name: str = "", votes: int = 0, percentage: float = 0):
        super().__init__()
        self.setStyleSheet("""
            WinnerBanner {
                background-color: #ECFDF5;
                border: 2px solid #A7F3D0;
                border-radius: 16px;
            }
        """)
        self.setFixedHeight(120)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Trophy
        trophy = QLabel("🏆")
        trophy.setFont(QFont("Segoe UI", 40))
        trophy.setFixedSize(70, 70)
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Avatar placeholder (orange circle)
        avatar = QLabel()
        avatar.setFixedSize(70, 70)
        avatar.setStyleSheet("background-color: #F59E0B; border-radius: 35px;")

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        winner_label = QLabel("Winner")
        winner_label.setFont(QFont("Segoe UI", 11))
        winner_label.setStyleSheet("color: #6B7280;")

        self.name_lbl = QLabel(name)
        self.name_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet("color: #111827;")

        self.votes_lbl = QLabel(f"Total Votes: {votes} ({percentage:.0f}%)")
        self.votes_lbl.setFont(QFont("Segoe UI", 11))
        self.votes_lbl.setStyleSheet("color: #6B7280;")

        info_layout.addWidget(winner_label)
        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.votes_lbl)

        layout.addWidget(trophy)
        layout.addWidget(avatar)
        layout.addLayout(info_layout)
        layout.addStretch()

    def set_winner(self, name: str, votes: int, percentage: float):
        self.name_lbl.setText(name)
        self.votes_lbl.setText(f"Total Votes: {votes} ({percentage:.0f}%)")

# views_signup.py
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QFont, QCursor

class SignupView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduVote Registration")
        self.resize(1000, 650)
        self.init_ui()

    def init_ui(self):
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT SIDE: BANNER
        self.banner_widget = QLabel()
        self.banner_widget.setScaledContents(True)
        self.banner_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(base_dir, 'Assets', 'banner_bg.png')

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.banner_widget.setPixmap(pixmap)
        else:
            self.banner_widget.setText("EduVote\nMissing banner_bg.png in assets folder")
            self.banner_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.banner_widget.setStyleSheet("background-color: #1F2937; color: white; font-weight: bold;")

        # RIGHT SIDE: SIGNUP FORM
        right_container = QWidget()
        right_container.setObjectName("rightContainer")
        right_container.setStyleSheet("""
            #rightContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #F5F5F5, stop:0.3 #E8E8E8, stop:0.7 #C5E8C5, stop:1 #90EE90);
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- The White Floating Card ---
        signup_card = QFrame()
        signup_card.setObjectName("signupCard")
        signup_card.setFixedWidth(380)
        signup_card.setStyleSheet("""
            #signupCard {
                background-color: #FFFFFF;
                border-radius: 20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        signup_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(40, 35, 40, 35)
        card_layout.setSpacing(12)

        # Header
        header_label = QLabel("Create your account")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #1a1a1a; background: transparent;")
        card_layout.addWidget(header_label)

        sub_header = QLabel("Please fill in your details to register")
        sub_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_header.setFont(QFont("Arial", 10))
        sub_header.setStyleSheet("color: #666666; background: transparent; margin-bottom: 10px;")
        card_layout.addWidget(sub_header)

        # Inline message banner (hidden by default)
        self.message_label = QLabel()
        self.message_label.setVisible(False)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.message_label.setOpenExternalLinks(False)
        # allow clicking the close 'x' link
        self.message_label.linkActivated.connect(lambda _href: self.hide_message())
        card_layout.addWidget(self.message_label)

        # Input style
        input_style = """
            QLineEdit {
                border: 2px solid #22C55E;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #16A34A;
            }
        """

        # Input Fields
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Full Name")
        self.fullname_input.setStyleSheet(input_style)
        self.fullname_input.setFixedHeight(42)
        card_layout.addWidget(self.fullname_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet(input_style)
        self.email_input.setFixedHeight(42)
        card_layout.addWidget(self.email_input)

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Student ID")
        self.student_id_input.setStyleSheet(input_style)
        self.student_id_input.setFixedHeight(42)
        card_layout.addWidget(self.student_id_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.setFixedHeight(42)
        card_layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet(input_style)
        self.confirm_password_input.setFixedHeight(42)
        card_layout.addWidget(self.confirm_password_input)

        # Register Button
        self.register_btn = QPushButton("Register")
        self.register_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.register_btn.setFixedHeight(45)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22C55E, stop:1 #15803D);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 22px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16A34A, stop:1 #14532D);
            }
            QPushButton:pressed {
                background-color: #14532D;
            }
        """)
        card_layout.addWidget(self.register_btn)

        # Login Link
        self.login_label = QLabel()
        self.login_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_label.setText("Already have an account? <a href='#' style='color: #22C55E; text-decoration: underline;'>Login here</a>")
        self.login_label.setOpenExternalLinks(False)
        self.login_label.setStyleSheet("color: #666666; background: transparent; margin-top: 8px; font-size: 12px;")
        card_layout.addWidget(self.login_label)

        signup_card.setLayout(card_layout)
        right_layout.addWidget(signup_card)
        right_container.setLayout(right_layout)

        main_layout.addWidget(self.banner_widget, 4)
        main_layout.addWidget(right_container, 5)
        main_container.setLayout(main_layout)

    def get_fullname(self):
        return self.fullname_input.text()

    def get_email(self):
        return self.email_input.text()

    def get_student_id(self):
        return self.student_id_input.text()

    def get_password(self):
        return self.password_input.text()

    def get_confirm_password(self):
        return self.confirm_password_input.text()

    def show_error(self, message):
        self.show_message(message, kind='error')

    def show_success(self, message):
        self.show_message(message, kind='success')

    def show_message(self, message: str, kind: str = 'error', timeout: int = 4000):
        """Show an inline, styled message banner above the form.

        kind: 'error' or 'success'
        timeout: milliseconds to auto-hide (0 to disable)
        """
        if kind == 'success':
            bg = '#ECFDF5'
            border = '#10B981'
            color = '#064E3B'
            title = 'Success'
        else:
            bg = '#FFF1F2'
            border = '#EF4444'
            color = '#58111A'
            title = 'Error'

        # include a small close 'x' on the right
        html = f"<div style='padding:10px;'><b>{title}:</b> {message} <a href='#' style='float:right; color:{color}; text-decoration:none;'>✕</a></div>"
        self.message_label.setText(html)
        self.message_label.setStyleSheet(f"background:{bg}; border:1px solid {border}; color:{color}; border-radius:8px; padding:6px; margin-bottom:6px;")
        self.message_label.setVisible(True)

        # Auto-hide after timeout if requested
        if timeout and timeout > 0:
            QTimer.singleShot(timeout, self.hide_message)

    def hide_message(self):
        self.message_label.setVisible(False)

    def resizeEvent(self, event):
        pm = self.banner_widget.pixmap()
        if pm is not None and not pm.isNull():
            self.banner_widget.setPixmap(pm.scaled(
                self.banner_widget.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
        super().resizeEvent(event)

# view_login.py
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QFont, QCursor

class LoginView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduVote Login")
        self.resize(1000, 650)
        self.init_ui()

    def init_ui(self):
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =============================================
        # LEFT SIDE: THE GRAPHICAL BANNER
        # =============================================
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

        # =============================================
        # RIGHT SIDE: THE LOGIN FORM CONTAINER
        # =============================================
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
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setFixedWidth(380)
        login_card.setStyleSheet("""
            #loginCard {
                background-color: #FFFFFF;
                border-radius: 20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        login_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        # 1. Header Texts
        header_label = QLabel("Welcome Back")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #1a1a1a; background: transparent;")
        card_layout.addWidget(header_label)

        sub_header = QLabel("Please login to cast your vote")
        sub_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_header.setFont(QFont("Arial", 10))
        sub_header.setStyleSheet("color: #666666; background: transparent; margin-bottom: 15px;")
        card_layout.addWidget(sub_header)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #DC2626; background: transparent; font-size: 12px;")
        self.status_label.hide()
        card_layout.addWidget(self.status_label)

        # Input style
        input_style = """
            QLineEdit {
                border: 2px solid #22C55E;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #16A34A;
            }
        """

        # 2. Input Fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(input_style)
        self.username_input.setFixedHeight(45)
        card_layout.addWidget(self.username_input)

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Student ID")
        self.student_id_input.setStyleSheet(input_style)
        self.student_id_input.setFixedHeight(45)
        card_layout.addWidget(self.student_id_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.setFixedHeight(45)
        card_layout.addWidget(self.password_input)

        # 3. Forgot Password Link
        forgot_pass_btn = QPushButton("Forgot Password?")
        forgot_pass_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        forgot_pass_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666666;
                background: transparent;
                font-size: 12px;
            }
            QPushButton:hover { color: #333333; }
        """)
        fp_layout = QHBoxLayout()
        fp_layout.addStretch()
        fp_layout.addWidget(forgot_pass_btn)
        card_layout.addLayout(fp_layout)

        # 4. Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.setFixedHeight(45)
        self.login_btn.setStyleSheet("""
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
        card_layout.addWidget(self.login_btn)

        # 5. Register Link (disabled)
        self.register_label = QLabel()
        self.register_label.setVisible(False)

        login_card.setLayout(card_layout)
        right_layout.addWidget(login_card)
        right_container.setLayout(right_layout)

        # =============================================
        # ASSEMBLE MAIN LAYOUT
        # =============================================
        main_layout.addWidget(self.banner_widget, 4)
        main_layout.addWidget(right_container, 5)
        main_container.setLayout(main_layout)

    # =============================================
    # HELPER METHODS FOR THE MVC CONTROLLER
    # =============================================
    def get_username(self):
        return self.username_input.text()

    def get_student_id(self):
        return self.student_id_input.text()

    def get_password(self):
        return self.password_input.text()

    def clear_inputs(self):
        self.username_input.clear()
        self.student_id_input.clear()
        self.password_input.clear()
        self.show_status("", is_error=False)

    def show_status(self, message: str, is_error: bool = True):
        if not message:
            self.status_label.hide()
            return
        color = "#DC2626" if is_error else "#16A34A"
        self.status_label.setStyleSheet(f"color: {color}; background: transparent; font-size: 12px;")
        self.status_label.setText(message)
        self.status_label.show()

    def resizeEvent(self, event):
        if not self.banner_widget.pixmap().isNull():
            self.banner_widget.setPixmap(self.banner_widget.pixmap().scaled(
                self.banner_widget.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
        super().resizeEvent(event)
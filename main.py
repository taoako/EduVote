
import sys
from PyQt6.QtWidgets import QApplication
from Views.views_login import LoginView
from Controller.controller_login import LoginController

GLOBAL_STYLES = """
    QMessageBox {
        background-color: #FFFFFF;
        color: #111827;
        border-radius: 10px;
    }
    QMessageBox QLabel {
        color: #111827;
    }
    QMessageBox QPushButton {
        background-color: #F3F4F6;
        color: #111827;
        border: 1px solid #E5E7EB;
        padding: 6px 12px;
        border-radius: 8px;
    }
    QMessageBox QPushButton:hover {
        background-color: #E5E7EB;
    }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(GLOBAL_STYLES)

   
    login_view = LoginView()
    login_controller = LoginController(login_view, signup_view=None)


    login_view.show()

    sys.exit(app.exec())



import re
from Models.model_db import Database


class SignupController:
    def __init__(self, view, login_view=None):
        self.view = view
        self.login_view = login_view
        self.db = Database()
        self.view.register_btn.clicked.connect(self.handle_signup)

        # Connect navigation back to login if label exists
        if hasattr(self.view, "login_label") and self.login_view is not None:
            self.view.login_label.linkActivated.connect(self.go_to_login)

    def go_to_login(self, _link: str = ""):
        """Switch from signup window back to login window."""
        if self.login_view is not None:
            self.view.hide()
            self.login_view.show()

    def is_valid_email(self, email: str) -> bool:
        # Accepts common email formats like: user@domain.com, user.name@school.edu.ph
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

    def handle_signup(self):
        full_name = self.view.get_fullname().strip()
        email = self.view.get_email().strip()
        student_id = self.view.get_student_id().strip()
        password = self.view.get_password()
        confirm_password = self.view.get_confirm_password()

        # Validation - collect missing fields for friendlier feedback
        fields = [
            ("Full Name", full_name, self.view.fullname_input),
            ("Email", email, self.view.email_input),
            ("Student ID", student_id, self.view.student_id_input),
            ("Password", password, self.view.password_input),
            ("Confirm Password", confirm_password, self.view.confirm_password_input),
        ]

        missing = [name for (name, val, _w) in fields if not val]
        if missing:
            if len(missing) == 1:
                msg = f"Please enter your {missing[0]}."
            else:
                msg = "Please complete the following fields: " + ", ".join(missing)
            # focus first empty field
            for (name, val, widget) in fields:
                if not val:
                    try:
                        widget.setFocus()
                    except Exception:
                        pass
                    break
            self.view.show_error(msg)
            return

        if not self.is_valid_email(email):
            self.view.show_error("Invalid email format!\nExample: yourname@school.com")
            return

        if len(password) < 6:
            self.view.show_error("Password must be at least 6 characters!")
            return

        if password != confirm_password:
            self.view.show_error("Passwords do not match!")
            return

        # Register user in database using Database service
        success, message = self.db.register_user(full_name, email, student_id, password)

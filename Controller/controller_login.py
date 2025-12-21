from Models.model_db import Database
from Views.main_window import MainWindow
from Views.admin import AdminMainWindow


class LoginController:
    def __init__(self, view, signup_view=None):
        self.view = view
        self.db = Database()
        # Keep a reference to the dashboard so it doesn't get garbage collected
        self.dashboard = None
        self.view.login_btn.clicked.connect(self.handle_login)

    @staticmethod
    def _normalize_user_data(user_data: dict | None) -> dict:
        """
        Normalize DB/user dict keys to what the UI expects.

        The SQLAlchemy User.to_dict() returns keys like 'user_id' and 'full_name',
        while the student/admin windows expect 'id' and 'name'.
        """
        user_data = user_data or {}
        user_id = user_data.get("id") or user_data.get("user_id")
        name = user_data.get("name") or user_data.get("full_name") or user_data.get("username")
        normalized = dict(user_data)
        normalized["id"] = user_id
        normalized["name"] = name
        return normalized

    def handle_login(self):
        username = self.view.get_username().strip()
        student_id = self.view.get_student_id().strip()
        password = self.view.get_password()

        if not username or not student_id or not password:
            self.view.show_status("All fields are required!")
            return

        success, user_data = self.db.authenticate_user(username, student_id, password)

        if success:
            user_data = self._normalize_user_data(user_data)
            self.view.show_status("", is_error=False)
            self.view.hide()

            # Check user role and open appropriate dashboard
            user_role = user_data.get("role", "student") if user_data else "student"
            
            if user_role == "admin":
                # Show admin panel for admin users
                self.dashboard = AdminMainWindow(user_data, on_logout=self._logout_to_login)
            else:
                # Show regular student dashboard
                self.dashboard = MainWindow(user_data, on_logout=self._logout_to_login)
            
            self.dashboard.show()
        else:
            self.view.show_status("Invalid username, student ID, or password.")

    def _logout_to_login(self):
        if self.dashboard:
            # Close and dereference the dashboard window
            self.dashboard.close()
            self.dashboard = None

        # Return to the login screen and clear any error message
        self.view.show()
        if hasattr(self.view, "clear_inputs"):
            self.view.clear_inputs()
        else:
            self.view.show_status("", is_error=False)
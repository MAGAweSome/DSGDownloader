import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import os

# Set a display variable for the test environment
if os.environ.get("DISPLAY", "") == "":
    print("no display found. Using :0.0")
    os.environ.__setitem__("DISPLAY", ":0.0")


from src.ui.main_window import get_user_selection


class TestMainWindow(unittest.TestCase):
    @patch("customtkinter.CTk")
    @patch("src.ui.main_window.messagebox")
    def test_on_submit_no_selection(self, mock_messagebox, mock_ctk):
        # Mock the entire customtkinter App
        mock_app_instance = MagicMock()
        mock_ctk.return_value = mock_app_instance

        # Mock the UI elements that return values
        with patch(
            "src.ui.main_window.create_dsg_prep_tab",
            return_value=({}, {}),
        ), patch(
            "src.ui.main_window.create_dsg_editions_tab",
            return_value=({}, {}),
        ), patch(
            "src.ui.main_window.create_schedules_tab",
            return_value=({}, MagicMock(get=lambda: False), MagicMock(get=lambda: False), MagicMock(get=lambda: False)),
        ), patch(
            "src.ui.main_window.create_ministers_tab",
            return_value={},
        ), patch(
            "src.ui.main_window.create_settings_tab",
            return_value=(MagicMock(), MagicMock(), MagicMock(), MagicMock()),
        ):
            # Call the function that creates the UI and triggers the submit
            result = get_user_selection()

            # Find the on_submit function and call it
            # This is a bit tricky as it's defined inside another function
            # We can inspect the mock calls to find it.
            # The submit button command is what we are after.
            on_submit_func = None
            for call in mock_app_instance.mock_calls:
                if "CTkButton" in str(call):
                    kwargs = call.kwargs
                    if kwargs.get("text") == "Submit":
                        on_submit_func = kwargs["command"]
                        break
            
            if on_submit_func:
                on_submit_func()

            # Assert that the warning was shown
            mock_messagebox.showwarning.assert_called_once_with(
                "No Selection",
                "You have not selected anything to download. Please make a selection or cancel.",
            )

            # Assert that the app was not destroyed
            mock_app_instance.destroy.assert_not_called()

            # Assert that the result is empty
            self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()

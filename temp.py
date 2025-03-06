from PyQt6.QtCore import QObject, pyqtSlot
import importlib
import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMessageBox

class PyHandler(QObject):
    """
    A QObject-derived class that exposes Python methods to JavaScript via QWebChannel.
    Methods are dynamically added based on the JSON configuration.
    """
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    @pyqtSlot(str, result=str)
    def process_message(self, message):
        """
        Process a message from JavaScript and return a response
        """
        try:
            from PyQt6.QtWidgets import QApplication
            import numpy as np
            exit_app = message == 'EXIT_APPLICATION'
            print('Exiting application...' if exit_app else f'Received message from JavaScript: {message}')
            QApplication.instance().quit() if exit_app else None
            return 'Exiting...' if exit_app else f"Python received: '{message}'. Here's a random number: {np.random.randint(1, 100)}"
        except Exception as e:
            print(f"Error executing process_message: {e}")
            return ""

    @pyqtSlot(str, str, result=bool)
    def show_dialog(self, title, message):
        """
        Show a dialog window with the given title and message
        """
        try:
            print(f"Showing dialog: {title} - {message}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self.main_window, title, message)
            return True
        except Exception as e:
            print(f"Error executing show_dialog: {e}")
            return False

    @pyqtSlot(result=str)
    def get_system_info(self):
        """
        Get basic system information
        """
        try:
            import platform
            return f"OS: {platform.system()} {platform.release()}, Python: {platform.python_version()}"
        except Exception as e:
            print(f"Error executing get_system_info: {e}")
            return ""

    @pyqtSlot(result=bool)
    def exit_application(self):
        """
        Exit the application
        """
        try:
            print("Exiting application...")
            import sys
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().quit()
            return True
        except Exception as e:
            print(f"Error executing exit_application: {e}")
            return False


def create_handler(main_window=None, parent=None):
    """
    Create and return an instance of the PyHandler class.
    This function is called from main.py to get the handler instance.
    """
    return PyHandler(main_window, parent)

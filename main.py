import os
import sys
import json
import time
from pathlib import Path
import numpy as np
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, QSize, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QProgressDialog, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtGui import QIcon
import types


class DynamicMethod(QObject):
    """A wrapper class for dynamic methods that can be exposed to JavaScript"""
    
    def __init__(self, code, parent=None):
        super().__init__(parent)
        self.code = code
        self.parent = parent
    
    @pyqtSlot(str, result=str)
    def process_message(self, message):
        """Process a message from JavaScript and return a response"""
        try:
            # Create a local namespace with access to self and parameters
            local_vars = {'self': self.parent, 'message': message}
            # Execute the code in this context
            exec(f"result = {self.code}", globals(), local_vars)
            # Return the result
            return local_vars.get('result', '')
        except Exception as e:
            print(f"Error executing process_message: {e}")
            return f"Error: {str(e)}"
    
    @pyqtSlot(str, str, result=bool)
    def show_dialog(self, title, message):
        """Show a dialog window with the given title and message"""
        try:
            # Create a local namespace with access to self and parameters
            local_vars = {'self': self.parent, 'title': title, 'message': message}
            # Execute the code in this context
            exec(f"result = {self.code}", globals(), local_vars)
            # Return the result
            return local_vars.get('result', False)
        except Exception as e:
            print(f"Error executing show_dialog: {e}")
            return False
    
    @pyqtSlot(result=str)
    def get_system_info(self):
        """Get system information"""
        try:
            # Create a local namespace with access to self
            local_vars = {'self': self.parent}
            # Execute the code in this context
            exec(f"result = {self.code}", globals(), local_vars)
            # Return the result
            return local_vars.get('result', '')
        except Exception as e:
            print(f"Error executing get_system_info: {e}")
            return f"Error: {str(e)}"


class DynamicPyBridge(QObject):
    """Dynamic Python handler that loads functions from a JSON configuration file"""
    
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.functions = {}
        # We'll load the config later when the loading dialog is shown
        self.config_path = config_path
    
    def load_config_with_progress(self, progress_dialog):
        """Load the bridge functions from the JSON configuration file with progress updates"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            functions = config.get('functions', [])
            total_functions = len(functions)
            
            if total_functions == 0:
                progress_dialog.setValue(100)
                return
            
            for i, func in enumerate(functions):
                # Update progress dialog
                name = func['name']
                progress_dialog.setLabelText(f"Loading function: {name}")
                progress_percent = int((i / total_functions) * 100)
                progress_dialog.setValue(progress_percent)
                
                # Process the function
                code = func.get('code', 'return None')
                self.functions[name] = code
                
                # Add a small delay to make the progress visible
                QApplication.processEvents()
                time.sleep(0.3)  # Simulate loading time
            
            # Set to 100% when done
            progress_dialog.setValue(100)
            print(f"Loaded {len(self.functions)} functions from configuration")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            progress_dialog.cancel()
    
    def _execute_function(self, func_name, local_vars=None):
        """Execute a function from the configuration"""
        if local_vars is None:
            local_vars = {}
        
        # Add self to the local variables
        local_vars['self'] = self
        
        if func_name in self.functions:
            try:
                # Create a wrapper function to execute the code
                exec_code = f"""
def _temp_func({', '.join(local_vars.keys())}):
    {self.functions[func_name]}
result = _temp_func({', '.join(local_vars.keys())})
"""
                # Execute the code in this context
                exec(exec_code, globals(), local_vars)
                # Return the result
                return local_vars.get('result')
            except Exception as e:
                print(f"Error executing {func_name}: {e}")
                return None
        return None
    
    @pyqtSlot(str, result=str)
    def process_message(self, message):
        """Process a message from JavaScript and return a response"""
        result = self._execute_function('process_message', {'message': message, 'np': np})
        if result is not None:
            return result
        return "Function not found or error occurred"
    
    @pyqtSlot(str, str, result=bool)
    def show_dialog(self, title, message):
        """Show a dialog window with the given title and message"""
        result = self._execute_function('show_dialog', {
            'title': title, 
            'message': message, 
            'QMessageBox': QMessageBox,
            'main_window': self.main_window
        })
        if result is not None:
            return bool(result)
        return False
    
    @pyqtSlot(result=str)
    def get_system_info(self):
        """Get system information"""
        result = self._execute_function('get_system_info', {'platform': __import__('platform')})
        if result is not None:
            return result
        return "Function not found or error occurred"


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("PyQt6 WebView Application")
        self.setFixedSize(1280, 720)
        
        # Center the window on the screen
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Create the WebView
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        
        # Set up the Python-JavaScript bridge
        self.channel = QWebChannel()
        
        # Create the bridge with the config path
        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "appdata" / "bridge_config.json"
        self.bridge = DynamicPyBridge(config_path, self)
        
        # Show loading dialog and load the configuration
        self.show_loading_dialog()
        
        # Register the bridge with the channel
        self.channel.registerObject("handler", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Load the HTML file
        html_path = base_dir / "appdata" / "index.html"
        self.web_view.load(QUrl.fromLocalFile(str(html_path)))
        
        # Connect signals
        self.web_view.loadFinished.connect(self.on_load_finished)
    
    def show_loading_dialog(self):
        """Show a loading dialog with a progress bar while loading the configuration"""
        # Create a progress dialog
        progress = QProgressDialog("Loading functions from configuration...", None, 0, 100, self)
        progress.setWindowTitle("Loading Configuration")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.setAutoClose(True)
        progress.setCancelButton(None)  # No cancel button
        progress.setMinimumWidth(400)
        
        # Show the dialog
        progress.show()
        QApplication.processEvents()
        
        # Load the configuration with progress updates
        self.bridge.load_config_with_progress(progress)
        
        # Close the dialog when done
        progress.close()
    
    def on_load_finished(self, ok):
        if ok:
            print("Page loaded successfully")
        else:
            print("Failed to load the page")


def main():
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
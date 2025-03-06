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
import importlib
import atexit


class DynamicPyBridge(QObject):
    """Dynamic Python handler that loads functions from a JSON configuration file"""
    
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.functions = {}
        self.config_path = config_path
        self.handler = None
        self.json_config = None
    
    def load_config_with_progress(self, progress_dialog):
        """Load the bridge functions from the JSON configuration file with progress updates"""
        try:
            # First, load the JSON configuration
            with open(self.config_path, 'r') as f:
                self.json_config = json.load(f)
            
            functions = self.json_config.get('functions', [])
            total_functions = len(functions)
            
            if total_functions == 0:
                progress_dialog.setValue(100)
                return
            
            # Store the functions for reference
            for i, func in enumerate(functions):
                # Update progress dialog
                name = func['name']
                progress_dialog.setLabelText(f"Loading function: {name}")
                progress_percent = int((i / total_functions) * 50)  # First half of progress
                progress_dialog.setValue(progress_percent)
                
                # Store the function code
                code = func.get('code', 'return None')
                self.functions[name] = code
                
                # Add a small delay to make the progress visible
                QApplication.processEvents()
                time.sleep(0.1)  # Simulate loading time
            
            # Now generate the temp.py file with the PyHandler class
            progress_dialog.setLabelText("Generating PyHandler class...")
            progress_dialog.setValue(60)
            QApplication.processEvents()
            
            self._generate_temp_py_file()
            
            # Import or reload the temp module
            progress_dialog.setLabelText("Loading PyHandler module...")
            progress_dialog.setValue(80)
            QApplication.processEvents()
            
            if "temp" in sys.modules:
                importlib.reload(sys.modules["temp"])
            else:
                import temp
            
            # Create an instance of the PyHandler class
            progress_dialog.setLabelText("Creating PyHandler instance...")
            progress_dialog.setValue(90)
            QApplication.processEvents()
            
            self.handler = sys.modules["temp"].create_handler(self.main_window, self)
            
            # Set to 100% when done
            progress_dialog.setValue(100)
            print(f"Loaded {len(self.functions)} functions from configuration")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            progress_dialog.cancel()
    
    def _generate_temp_py_file(self):
        """Generate the temp.py file with the PyHandler class based on the JSON configuration"""
        if not self.json_config:
            print("No JSON configuration loaded")
            return
        
        # Start building the PyHandler class
        py_handler_code = """from PyQt6.QtCore import QObject, pyqtSlot
import importlib
import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMessageBox

class PyHandler(QObject):
    \"\"\"
    A QObject-derived class that exposes Python methods to JavaScript via QWebChannel.
    Methods are dynamically added based on the JSON configuration.
    \"\"\"
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
"""
        
        # Add each function from the JSON to the PyHandler class
        for func in self.json_config.get('functions', []):
            name = func['name']
            code = func.get('code', 'return None')
            parameters = func.get('parameters', [])
            return_type = func.get('return_type', 'str')
            
            # Create the method with the appropriate pyqtSlot decorator
            # Ensure proper syntax for the pyqtSlot decorator
            param_types = []
            for _ in parameters:
                param_types.append('str')  # Default to str for all parameters
            
            # Create the decorator with proper syntax
            if param_types:
                decorator = f"@pyqtSlot({', '.join(param_types)}, result={return_type})"
            else:
                decorator = f"@pyqtSlot(result={return_type})"
            
            # Debug: Print the function details
            print(f"Generating method: {name}, Parameters: {parameters}, Return type: {return_type}")
            print(f"Decorator: {decorator}")
            
            # Ensure the code is properly indented and doesn't contain syntax errors
            # Split the code into lines and indent each line
            code_lines = code.split(';')
            indented_code = []
            for line in code_lines:
                line = line.strip()
                if line:
                    indented_code.append(f"            {line}")
            
            # Join the lines with newlines for better readability
            indented_code_str = '\n'.join(indented_code)
            
            method_code = f"""
    {decorator}
    def {name}({', '.join(['self'] + parameters)}):
        \"\"\"
        {func.get('description', f'Implementation of {name}')}
        \"\"\"
        try:
{indented_code_str}
        except Exception as e:
            print(f"Error executing {name}: {{e}}")
            return {'""' if return_type == 'str' else 'False' if return_type == 'bool' else 'None'}
"""
            py_handler_code += method_code
        
        # Add the create_handler function
        py_handler_code += """

def create_handler(main_window=None, parent=None):
    \"\"\"
    Create and return an instance of the PyHandler class.
    This function is called from main.py to get the handler instance.
    \"\"\"
    return PyHandler(main_window, parent)
"""
        
        # Write the PyHandler class to temp.py
        with open("temp.py", "w") as f:
            f.write(py_handler_code)
        
        # Debug: Print the generated file
        print("Generated temp.py with PyHandler class")
        try:
            # Try to compile the generated code to check for syntax errors
            with open("temp.py", "r") as f:
                source = f.read()
            compile(source, "temp.py", "exec")
            print("Compilation successful: No syntax errors in generated code")
        except SyntaxError as e:
            print(f"Compilation failed: Syntax error in generated code: {e}")
            # Print the problematic line
            lines = source.split('\n')
            if e.lineno <= len(lines):
                print(f"Line {e.lineno}: {lines[e.lineno-1]}")
    
    def get_handler(self):
        """Get the PyHandler instance"""
        if self.handler is None:
            # If handler is not created yet, we need to load the configuration first
            print("Handler not initialized. Please load the configuration first.")
            return None
        return self.handler


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Register cleanup function to be called on exit
        atexit.register(self.cleanup)
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Serverless Desktop Python v0.1")
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
        
        # Register the PyHandler instance directly with the channel
        # This allows JavaScript to access the PyHandler methods directly
        handler = self.bridge.get_handler()
        if handler:
            self.channel.registerObject("pythonHandler", handler)
        else:
            print("Warning: No handler available to register with QWebChannel")
        
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
    
    def cleanup(self):
        """Clean up resources before exiting"""
        print("Cleaning up before exit...")
        # Clear the temp.py file
        try:
            with open("temp.py", "w") as f:
                f.write("# This file was cleared on application exit\n")
            print("temp.py file cleared")
        except Exception as e:
            print(f"Error clearing temp.py: {e}")


def main():
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
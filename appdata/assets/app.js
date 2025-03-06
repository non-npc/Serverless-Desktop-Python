// Main JavaScript for the application

// This will be initialized once the QWebChannel is ready
let pythonHandler = null;

// Function to be called when QWebChannel is ready
function onQWebChannelReady() {
    // Wait for QWebChannel API to be available
    if (typeof QWebChannel !== "undefined") {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            // Get the Python handler object that was exposed
            pythonHandler = channel.objects.pythonHandler;
            
            if (pythonHandler) {
                console.log("QWebChannel initialized successfully with pythonHandler");
                // Now we can set up event listeners that use the Python handler
                setupEventListeners();
            } else {
                console.error("pythonHandler not available in QWebChannel");
                document.getElementById("response").textContent = "Error: Python handler not available. Please restart the application.";
            }
        });
    } else {
        console.error("QWebChannel not available");
    }
}

// Set up event listeners for UI elements
function setupEventListeners() {
    document.getElementById("callPythonBtn").addEventListener("click", function() {
        callPythonFunction("Hello from JavaScript!");
    });
    
    document.getElementById("showDialogBtn").addEventListener("click", function() {
        showPythonDialog("Message from JavaScript", "This dialog was triggered from JavaScript!");
    });
    
    document.getElementById("getSystemInfoBtn").addEventListener("click", function() {
        getSystemInfo();
    });
    
    document.getElementById("exitAppBtn").addEventListener("click", function() {
        exitApplication();
    });
}

// Call a Python function via the bridge
function callPythonFunction(message) {
    if (pythonHandler) {
        // Direct call to the process_message method
        pythonHandler.process_message(message, function(result) {
            document.getElementById("response").textContent = result;
        });
    } else {
        console.error("Python handler not available");
        document.getElementById("response").textContent = "Error: Python handler not available";
    }
}

// Show a Python dialog via the bridge
function showPythonDialog(title, message) {
    if (pythonHandler) {
        // Direct call to the show_dialog method
        pythonHandler.show_dialog(title, message, function(result) {
            if (result) {
                document.getElementById("response").textContent = "Dialog shown successfully";
            } else {
                document.getElementById("response").textContent = "Failed to show dialog";
            }
        });
    } else {
        console.error("Python handler not available");
        document.getElementById("response").textContent = "Error: Python handler not available";
    }
}

// Get system information via the bridge
function getSystemInfo() {
    if (pythonHandler) {
        // Direct call to the get_system_info method
        pythonHandler.get_system_info(function(result) {
            document.getElementById("response").textContent = "System Info: " + result;
        });
    } else {
        console.error("Python handler not available");
        document.getElementById("response").textContent = "Error: Python handler not available";
    }
}

// Exit the application via the bridge
function exitApplication() {
    if (pythonHandler) {
        document.getElementById("response").textContent = "Exiting application...";
        // Use exit_application method if available, otherwise fall back to process_message
        if (typeof pythonHandler.exit_application === 'function') {
            pythonHandler.exit_application(function(result) {
                console.log("Exit result:", result);
            });
        } else {
            // Fallback to process_message
            pythonHandler.process_message("EXIT_APPLICATION", function(result) {
                console.log("Exit result:", result);
            });
        }
    } else {
        console.error("Python handler not available");
        document.getElementById("response").textContent = "Error: Python handler not available";
    }
}

// Initialize QWebChannel when the document is ready
document.addEventListener("DOMContentLoaded", function() {
    if (window.QWebChannel) {
        onQWebChannelReady();
    } else {
        console.error("QWebChannel not loaded");
    }
}); 
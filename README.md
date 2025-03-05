# Serverless-Desktop-Python
A serverless desktop python demo for games and apps


## Screenshot

![Live Code Previewer Screenshot-01](screenshot-01.png)
![Live Code Previewer Screenshot-02](screenshot-02.png)

## Features

- **Python/JS Bridge**: Communication bridge for Python->JS and JS->Python.
- **External Methods Example**: An example of using python code in a JSON file.
- **Manual Update Option**: You can disable live updating by unchecking the "Toggle Live Updating" checkbox. In this mode, the webview is updated only when you click the "Load in Webview" button.
- **HTML, CSS, and JavaScript Support**: You can input not just HTML, but also include CSS and JavaScript directly in the text area for live rendering.
- **Local File Support**: Local images/scripts/etc work relative to the app folder or using absolute paths (see "Local File Support" below for details).

## Installation

You can install the dependencies using pip:

\`\`\`
pip install PyQt6 PyQtWebEngine
pip install numpy
\`\`\`

## Usage

1. Clone this repository:
   \`\`\`
   git clone https://github.com/non-npc/Serverless-Desktop-Python.git
   cd Serverless-Desktop-Python
   \`\`\`

2. Run the application:

   \`\`\`
   python main.py
   \`\`\`

## NOTES
This project uses the python bridge methods in an external JSON file.
This is so that you can distribute the compiled EXE and JSON file together without having to modify the compiled EXE, each time you want to make a change to the config or a method based on changes in your HTMl/JS.


## Contributing

Contributions are welcome! If you'd like to contribute to the project, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.


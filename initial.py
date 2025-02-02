import sys
import pandas as pd
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QComboBox, QWidget, 
    QHBoxLayout, QLabel, QTextEdit, QSplitter, QTableWidget, QTableWidgetItem
)
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt, QThread, Signal
from NodeGraphQt import NodeGraph, BaseNode

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Adjust API endpoint if needed

class InputNode(BaseNode):
    __identifier__ = "custom.nodes"
    NODE_NAME = "Input Node"

    def __init__(self):
        super(InputNode, self).__init__()
        self.add_output("DataFrame")
        self.add_text_input("file_path", "File Path:")
        self._data = None

    def load_data(self):
        file_path = self.get_property("file_path")
        try:
            self._data = pd.read_csv(file_path)
            print(f"Data loaded:\n{self._data.head()}")
        except Exception as e:
            print(f"Error loading data: {e}")

    def on_property_changed(self, name, value):
        if name == "file_path":
            self.load_data()

class CodeGenerationThread(QThread):
    result_ready = Signal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            response = requests.post(OLLAMA_API_URL, json={"model": "qwen2.5-coder:3b", "prompt": self.query, "stream": False})
            if response.status_code == 200:
                generated_code = response.json().get("response", "Error generating code")
                self.result_ready.emit(generated_code)
            else:
                self.result_ready.emit("Error connecting to Ollama API")
        except Exception as e:
            self.result_ready.emit(f"Request failed: {e}")

class CalculationNode(BaseNode):
    __identifier__ = "custom.nodes"
    NODE_NAME = "Calculation Node"

    def __init__(self):
        super(CalculationNode, self).__init__()
        self.add_input("DataFrame")
        self.add_output("Calculated DataFrame")
        self.add_text_input("formula", "Formula:")
        self.add_text_input("query", "Describe Calculation:")

    def apply_calculation(self, df):
        formula = self.get_property("formula")
        try:
            df["Result"] = eval(formula, {}, {"df": df})
            print(f"Calculated Data:\n{df.head()}")
            return df
        except Exception as e:
            print(f"Error in calculation: {e}")
            return df

class NodeGraphApp(QMainWindow):
    def __init__(self):
        super(NodeGraphApp, self).__init__()
        self.setWindowTitle("Node-Based Data Analytics Editor")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        toolbar_layout = QHBoxLayout()
        self.add_node_button = QPushButton("Add Node")
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItems(["Input Node", "Calculation Node"])
        self.process_graph_button = QPushButton("Process Graph")
        self.run_button = QPushButton("Run Query")
        toolbar_layout.addWidget(self.add_node_button)
        toolbar_layout.addWidget(self.node_type_combo)
        toolbar_layout.addWidget(self.process_graph_button)
        toolbar_layout.addWidget(self.run_button)

        self.splitter = QSplitter(Qt.Vertical)
        self.graph = NodeGraph()
        self.graph_widget = self.graph.widget
        self.splitter.addWidget(self.graph_widget)

        self.output_splitter = QSplitter(Qt.Horizontal)

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setPlaceholderText("Generated code will appear here...")
        self.output_splitter.addWidget(self.output_console)

        self.dataframe_output = QTableWidget()
        self.output_splitter.addWidget(self.dataframe_output)

        self.splitter.addWidget(self.output_splitter)

        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.splitter)

        self.graph_widget.installEventFilter(self)

        self.graph.register_node(InputNode)
        self.graph.register_node(CalculationNode)

        self.add_node_button.clicked.connect(self.add_node)
        self.process_graph_button.clicked.connect(self.process_graph)
        self.run_button.clicked.connect(self.run_selected_calculation_node)

    def add_node(self):
        node_type = self.node_type_combo.currentText()
        if node_type == "Input Node":
            node = self.graph.create_node("custom.nodes.InputNode")
        elif node_type == "Calculation Node":
            node = self.graph.create_node("custom.nodes.CalculationNode")
        else:
            return
        node.set_pos(0, 0)

    def process_graph(self):
        nodes = self.graph.all_nodes()
        input_nodes = [node for node in nodes if isinstance(node, InputNode)]
        if not input_nodes:
            print("No Input Nodes found!")
            return
        for input_node in input_nodes:
            self.process_node(input_node, None)

    def process_node(self, node, incoming_data):
        if isinstance(node, InputNode):
            node.load_data()
            data = node._data
        elif isinstance(node, CalculationNode):
            if incoming_data is not None:
                data = node.apply_calculation(incoming_data)
                self.display_dataframe(data)
            else:
                print("Calculation Node has no incoming data!")
                return
        else:
            print(f"Unknown node type: {type(node)}")
            return
        for output_port in node.output_ports():
            connected_ports = output_port.connected_ports()
            for connected_port in connected_ports:
                next_node = connected_port.node()
                self.process_node(next_node, data)

    def run_selected_calculation_node(self):
        selected_nodes = self.graph.selected_nodes()
        if not selected_nodes:
            print("No node selected!")
            return
        for node in selected_nodes:
            if isinstance(node, CalculationNode):
                query = node.get_property("query")
                if not query:
                    return
                self.output_console.setPlainText("Generating code...")
                self.worker_thread = CodeGenerationThread(query)
                self.worker_thread.result_ready.connect(self.update_output_console)
                self.worker_thread.start()
                return
        print("No Calculation Node selected!")

    def display_dataframe(self, df):
        self.dataframe_output.setRowCount(df.shape[0])
        self.dataframe_output.setColumnCount(df.shape[1])
        self.dataframe_output.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.dataframe_output.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

    def update_output_console(self, text):
        self.output_console.setPlainText(text)

    def eventFilter(self, obj, event):
        if event.type() == QWheelEvent.Wheel:
            if event.modifiers() == Qt.ControlModifier:
                factor = 1.2 if event.angleDelta().y() > 0 else 0.8
                self.graph_widget.scale(factor, factor)
                return True
        return super().eventFilter(obj, event)

def main():
    app = QApplication(sys.argv)
    window = NodeGraphApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

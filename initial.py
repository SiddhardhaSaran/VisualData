import sys
import pandas as pd
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QComboBox, QWidget, 
    QHBoxLayout, QLabel, QTextEdit, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QSpinBox, QFileDialog
)
from PySide6.QtGui import QWheelEvent, QPen, QBrush, QPolygonF
from PySide6.QtCore import Qt, QThread, Signal, QPointF
from NodeGraphQt import NodeGraph, BaseNode, BackdropNode

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Adjust API endpoint if needed


from NodeGraphQt import BaseNode

from NodeGraphQt import BaseNode
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor

from NodeGraphQt import BaseNode
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QGraphicsItem

from NodeGraphQt import BaseNode
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QGraphicsItem

from NodeGraphQt import BaseNode
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QCursor

class ResizableNode(BaseNode):
    __identifier__ = "custom.nodes"
    NODE_NAME = "Resizable Node"

    def __init__(self):
        super(ResizableNode, self).__init__()
        self.set_property("width", 800)  # Default width
        self.set_property("height", 950)  # Default height
        self.resizing = False
        self.update()

    def mousePressEvent(self, event):
        """Detect if clicking bottom-right corner to resize."""
        rect = self.bounding_rect()
        if rect.contains(event.pos()) and self.is_near_corner(event.pos()):
            self.resizing = True
            self.start_pos = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Resize the node when dragging."""
        if self.resizing:
            delta = event.pos() - self.start_pos
            new_width = max(80, self.get_property("width") + delta.x())  # Min size 80
            new_height = max(50, self.get_property("height") + delta.y())  # Min size 50

            self.set_property("width", new_width)
            self.set_property("height", new_height)
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Stop resizing when releasing mouse."""
        self.resizing = False
        super().mouseReleaseEvent(event)

    def is_near_corner(self, pos):
        """Check if mouse is near the bottom-right corner."""
        rect = self.bounding_rect()
        return rect.right() - 10 <= pos.x() <= rect.right() and rect.bottom() - 10 <= pos.y() <= rect.bottom()


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
                self.result_ready.emit("Error connecting to Ollama API.")
        except Exception as e:
            self.result_ready.emit(f"Either Ollama is not installed or not running \n. Request failed: {e}")

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
            return df, None
        except Exception as e:
            print(f"Error in calculation: {e}")
            return df, str(e)

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

     # --- OUTPUT TAB WIDGET ---
        self.output_tabs = QTabWidget()

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setPlaceholderText("Generated code will appear here...")
        self.output_tabs.addTab(self.output_console, "Generated Code")


        self.dataframe_output = QTableWidget()
        self.output_tabs.addTab(self.dataframe_output, "Data Preview")


      # Tab 3: Errors
        self.error_console = QTextEdit()
        self.error_console.setReadOnly(True)
        self.error_console.setPlaceholderText("Errors will appear here...")
        self.output_tabs.addTab(self.error_console, "Errors")

        self.splitter.addWidget(self.output_tabs)

        # Pagination Controls
        self.pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_size_selector = QSpinBox()
        self.page_size_selector.setRange(10, 1000)
        self.page_size_selector.setValue(100)
        self.page_label = QLabel("Page: 1")

        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_button)
        self.pagination_layout.addWidget(QLabel("Rows per page:"))
        self.pagination_layout.addWidget(self.page_size_selector)

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)


        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.splitter)
        main_layout.addLayout(self.pagination_layout)

        self.graph_widget.installEventFilter(self)

        self.graph.register_node(InputNode)
        self.graph.register_node(CalculationNode)

        
        self.add_node_button.clicked.connect(self.add_node)
        self.process_graph_button.clicked.connect(self.process_graph)
        self.run_button.clicked.connect(self.run_selected_calculation_node)

        self.save_button = QPushButton("Save Graph")
        self.load_button = QPushButton("Load Graph")
        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.load_button)

        self.add_backdrop_button = QPushButton("Add Backdrop")
        toolbar_layout.addWidget(self.add_backdrop_button)
        self.add_backdrop_button.clicked.connect(self.add_backdrop)


        self.save_button.clicked.connect(self.save_graph)
        self.load_button.clicked.connect(self.load_graph)
    
    def add_backdrop(self):
        backdrop = self.graph.create_node('nodeGraphQt.nodes.BackdropNode')
        backdrop.set_property('name', 'New Backdrop')
        backdrop.set_pos(50, 50)


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
            self.display_dataframe(data)
        elif isinstance(node, CalculationNode):
            if incoming_data is not None:
                data, error_message = node.apply_calculation(incoming_data)
                if error_message:
                    self.error_console.setPlainText(f"Error: {error_message}")
                    self.output_tabs.setCurrentIndex(2)
                else:
                    self.display_dataframe(data)
                    self.output_tabs.setCurrentIndex(1)
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

    def next_page(self):
        if self.current_df is None:
            return
        page_size = self.page_size_selector.value()
        max_page = len(self.current_df) // page_size  # Calculate max page index
        if self.current_page < max_page:
            self.current_page += 1
            self.page_label.setText(f"Page: {self.current_page + 1}")
            self.update_dataframe_view()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.page_label.setText(f"Page: {self.current_page + 1}")
            self.update_dataframe_view()

    def display_dataframe(self, df):
        self.current_df = df
        self.current_page = 0
        self.update_dataframe_view()

    def update_dataframe_view(self):
        if self.current_df is None:
            return
        page_size = self.page_size_selector.value()
        start_row = self.current_page * page_size
        end_row = start_row + page_size
        df_page = self.current_df.iloc[start_row:end_row]

        self.dataframe_output.setRowCount(df_page.shape[0])
        self.dataframe_output.setColumnCount(df_page.shape[1])
        self.dataframe_output.setHorizontalHeaderLabels(df_page.columns)
        for i in range(df_page.shape[0]):
            for j in range(df_page.shape[1]):
                self.dataframe_output.setItem(i, j, QTableWidgetItem(str(df_page.iat[i, j])))

    def update_output_console(self, text):
        self.output_console.setPlainText(text)

    def eventFilter(self, obj, event):
        if event.type() == QWheelEvent.Wheel:
            if event.modifiers() == Qt.ControlModifier:
                factor = 1.2 if event.angleDelta().y() > 0 else 0.8
                self.graph_widget.scale(factor, factor)
                return True
        return super().eventFilter(obj, event)

    def save_graph(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if file_path:
            self.graph.save_session(file_path)
            print(f"Graph saved to {file_path}")

    def load_graph(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if file_path:
            self.graph.load_session(file_path)
            print(f"Graph loaded from {file_path}")


def main():
    app = QApplication(sys.argv)
    window = NodeGraphApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

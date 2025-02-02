import sys
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QComboBox, QWidget, QHBoxLayout
from NodeGraphQt import NodeGraph, BaseNode


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

#File_path =/Users/bg/VisualAnalysis/train.csv


class FilterNode(BaseNode):
    __identifier__ = "custom.nodes"
    NODE_NAME = "Filter Node"

    def __init__(self):
        super(FilterNode, self).__init__()
        self.add_input("DataFrame")
        self.add_output("Filtered DataFrame")
        self.add_text_input("filter_condition", "Condition:")

    def apply_filter(self, df):
        condition = self.get_property("filter_condition")
        print(df.head)
        print(condition)
        try:
            filtered_df = df.query(condition)
            print(f"Filtered Data:\n{filtered_df.head()}")
            return filtered_df
        except Exception as e:
            print(f"Error applying filter: {e}")
            return df

    def on_property_changed(self, name, value):
        if name == "filter_condition":
            self.apply_filter()


class CalculationNode(BaseNode):
    __identifier__ = "custom.nodes"
    NODE_NAME = "Calculation Node"

    def __init__(self):
        super(CalculationNode, self).__init__()
        self.add_input("DataFrame")
        self.add_output("Calculated DataFrame")
        self.add_text_input("formula", "Formula:")

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

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Toolbar for adding nodes
        toolbar_layout = QHBoxLayout()
        self.add_node_button = QPushButton("Add Node")
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItems(["Input Node", "Filter Node", "Calculation Node"])
        self.process_graph_button = QPushButton("Process Graph")
        toolbar_layout.addWidget(self.add_node_button)
        toolbar_layout.addWidget(self.node_type_combo)
        toolbar_layout.addWidget(self.process_graph_button)

        main_layout.addLayout(toolbar_layout)

        # Node graph widget
        self.graph = NodeGraph()
        self.graph_widget = self.graph.widget
        main_layout.addWidget(self.graph_widget)

        # Register custom nodes
        self.graph.register_node(InputNode)
        self.graph.register_node(FilterNode)
        self.graph.register_node(CalculationNode)

        # Connect button signals
        self.add_node_button.clicked.connect(self.add_node)
        self.process_graph_button.clicked.connect(self.process_graph)

    def add_node(self):
        node_type = self.node_type_combo.currentText()
        if node_type == "Input Node":
            node = self.graph.create_node("custom.nodes.InputNode")
        elif node_type == "Filter Node":
            node = self.graph.create_node("custom.nodes.FilterNode")
        elif node_type == "Calculation Node":
            node = self.graph.create_node("custom.nodes.CalculationNode")
        else:
            return
        # Position new nodes at the center
        node.set_pos(0, 0)

    def process_graph(self):
        # Find all nodes
        nodes = self.graph.all_nodes()
        
        # Start from Input Nodes
        input_nodes = [node for node in nodes if isinstance(node, InputNode)]
        if not input_nodes:
            print("No Input Nodes found!")
            return
        
        # Process each input node
        for input_node in input_nodes:
            self.process_node(input_node, None)

    def process_node(self, node, incoming_data):
        if isinstance(node, InputNode):
            node.load_data()
            data = node._data
        elif isinstance(node, FilterNode):
            if incoming_data is not None:
                data = node.apply_filter(incoming_data)
            else:
                print("Filter Node has no incoming data!")
                return
        elif isinstance(node, CalculationNode):
            if incoming_data is not None:
                data = node.apply_calculation(incoming_data)
            else:
                print("Calculation Node has no incoming data!")
                return
        else:
            print(f"Unknown node type: {type(node)}")
            return
        
        # Pass data to connected nodes
        for output_port in node.output_ports():
            connected_ports = output_port.connected_ports()
            for connected_port in connected_ports:
                next_node = connected_port.node()
                self.process_node(next_node, data)



def main():
    app = QApplication(sys.argv)
    window = NodeGraphApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

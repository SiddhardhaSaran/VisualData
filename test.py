import sys
import json
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QLabel, QLineEdit, QPushButton, QGraphicsItemGroup, QGraphicsEllipseItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QColor, QBrush, QPainter

class Node(QGraphicsRectItem):
    def __init__(self, x, y, width, height, node_name="Node"):
        super().__init__(QRectF(x, y, width, height))
        self.setBrush(QBrush(QColor(200, 200, 255)))
        
        # Set up the name label for the node
        self.node_name = node_name
        self.label = QLabel(self.node_name)
        self.label.move(10, -20)  # Place it above the node
        self.label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.label.setAlignment(Qt.AlignCenter)
        
        # Set up the editable input box
        self.name_input = QLineEdit(self.node_name)
        self.name_input.setGeometry(10, 0, width - 20, 20)
        self.name_input.textChanged.connect(self.update_name)
        
        # Set the flags to make the node movable and resizable
        self.setFlag(QGraphicsRectItem.ItemIsMovable)  
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemIsDragEnabled)
        
        # Initialize the resizing logic
        self.resize_handle = QGraphicsEllipseItem(x + width - 10, y + height - 10, 10, 10, self)
        self.resize_handle.setBrush(QBrush(QColor(0, 0, 0)))
        self.resize_handle.setFlag(QGraphicsEllipseItem.ItemIsMovable)

    def update_name(self):
        """Update the name label when the user changes the input."""
        self.node_name = self.name_input.text()
        self.label.setText(self.node_name)
        
    def mouseMoveEvent(self, event):
        """Override mouse move event for resizing functionality."""
        super().mouseMoveEvent(event)
        if self.resize_handle.isUnderMouse():
            mouse_pos = event.scenePos()
            rect = self.rect()
            rect.setWidth(mouse_pos.x() - rect.left())
            rect.setHeight(mouse_pos.y() - rect.top())
            self.setRect(rect)
            self.resize_handle.setPos(rect.right() - 10, rect.bottom() - 10)

    def mouseReleaseEvent(self, event):
        """Override mouse release event to prevent unwanted resizing logic."""
        super().mouseReleaseEvent(event)
        if self.resize_handle.isUnderMouse():
            self.setFlag(QGraphicsRectItem.ItemIsMovable, True)

class GroupBox(QGraphicsItemGroup):
    def __init__(self, group_name="Group", x=0, y=0, width=200, height=200):
        super().__init__()
        self.group_name = group_name
        self.setFlag(QGraphicsItemGroup.ItemIsMovable)  # Allow moving the group
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable)

        # Create label for the group
        self.label = QLabel(self.group_name)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.move(0, -20)

        self.nodes = []
        self.setRect(x, y, width, height)

    def add_node(self, node):
        """Add a node to this group."""
        self.nodes.append(node)
        self.addToGroup(node)

    def set_group_name(self, name):
        """Set the name of the group."""
        self.group_name = name
        self.label.setText(self.group_name)

    def paint(self, painter, option, widget=None):
        """Custom painting to add background color to the group."""
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.setPen(QColor(100, 100, 100))
        painter.drawRect(self.rect())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Node-based UI")
        self.setGeometry(100, 100, 800, 600)
        
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        
        self.add_nodes_button = QPushButton('Add Node', self)
        self.add_nodes_button.clicked.connect(self.add_node)
        self.add_nodes_button.move(20, 20)
        
        self.add_group_button = QPushButton('Add Group', self)
        self.add_group_button.clicked.connect(self.add_group)
        self.add_group_button.move(120, 20)
        
        self.save_button = QPushButton('Save Graph', self)
        self.save_button.clicked.connect(self.save_graph)
        self.save_button.move(220, 20)
        
        self.load_button = QPushButton('Load Graph', self)
        self.load_button.clicked.connect(self.load_graph)
        self.load_button.move(320, 20)
        
        # Create an initial group
        self.group_box = GroupBox("Group 1", 50, 50, 300, 200)
        self.scene.addItem(self.group_box)
        
        self.nodes = []

    def add_node(self):
        """Add a new node."""
        node = Node(50, 50, 100, 40)
        self.nodes.append(node)
        self.scene.addItem(node)
        
    def add_group(self):
        """Create and add a new group."""
        group_name = "New Group"
        group = GroupBox(group_name, 400, 50, 300, 200)
        self.scene.addItem(group)

        # Add the first node to the group for demonstration
        if self.nodes:
            node = self.nodes[0]
            group.add_node(node)

    def save_graph(self):
        """Save the graph to a JSON file."""
        graph_data = {"nodes": [], "groups": []}
        
        # Save nodes
        for node in self.nodes:
            node_data = {"x": node.x(), "y": node.y(), "width": node.rect().width(), "height": node.rect().height(), "name": node.node_name}
            graph_data["nodes"].append(node_data)

        # Save groups
        for group in self.scene.items():
            if isinstance(group, GroupBox):
                group_data = {"x": group.x(), "y": group.y(), "width": group.rect().width(), "height": group.rect().height(), "name": group.group_name}
                graph_data["groups"].append(group_data)

        with open('graph_data.json', 'w') as f:
            json.dump(graph_data, f)

    def load_graph(self):
        """Load the graph from a JSON file."""
        with open('graph_data.json', 'r') as f:
            graph_data = json.load(f)
        
        # Clear the current scene
        self.scene.clear()
        
        # Recreate nodes
        for node_data in graph_data["nodes"]:
            node = Node(node_data["x"], node_data["y"], node_data["width"], node_data["height"], node_data["name"])
            self.nodes.append(node)
            self.scene.addItem(node)
        
        # Recreate groups
        for group_data in graph_data["groups"]:
            group = GroupBox(group_data["name"], group_data["x"], group_data["y"], group_data["width"], group_data["height"])
            self.scene.addItem(group)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())

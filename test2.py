import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsItemGroup, QPushButton, QGraphicsItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QColor, QBrush, QPen


class Node(QGraphicsRectItem):
    def __init__(self, x, y, width, height, node_name="Node"):
        super().__init__(QRectF(x, y, width, height))
        self.setBrush(QBrush(QColor(200, 200, 255)))
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

    def set_node_name(self, name):
        """Set the name of the node."""
        self.node_name = name


class GroupNode(QGraphicsRectItem):
    def __init__(self, nodes, x, y, width, height):
        super().__init__(QRectF(x, y, width, height))
        self.setBrush(QBrush(QColor(220, 220, 220)))
        self.setPen(QPen(QColor(0, 0, 0)))
        
        # Group the nodes inside this new group node
        self.nodes = nodes
        for node in nodes:
            node.setParentItem(self)  # Set parent for the nodes

        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)

    def set_node_name(self, name):
        """Set the name of the group node."""
        self.node_name = name


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Node-based UI")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        # Add buttons for node actions
        self.add_node_button = QPushButton('Add Node', self)
        self.add_node_button.clicked.connect(self.add_node)
        self.add_node_button.move(20, 20)

        self.group_button = QPushButton('Group Selected Nodes', self)
        self.group_button.clicked.connect(self.group_nodes)
        self.group_button.move(120, 20)

        self.nodes = []
        self.selected_nodes = []
        self.selection_rect = None

    def add_node(self):
        """Add a new node to the scene."""
        node = Node(50, 50, 100, 40)
        self.nodes.append(node)
        self.scene.addItem(node)

    def group_nodes(self):
        """Group selected nodes into one node."""
        if not self.selected_nodes:
            return
        
        # Create a bounding box around the selected nodes
        min_x = min(node.x() for node in self.selected_nodes)
        min_y = min(node.y() for node in self.selected_nodes)
        max_x = max(node.x() + node.rect().width() for node in self.selected_nodes)
        max_y = max(node.y() + node.rect().height() for node in self.selected_nodes)

        width = max_x - min_x
        height = max_y - min_y

        # Create the group node
        group = GroupNode(self.selected_nodes, min_x, min_y, width, height)
        self.scene.addItem(group)

        # Remove the original nodes from the scene
        for node in self.selected_nodes:
            self.scene.removeItem(node)

        # Clear the selection
        self.selected_nodes = []

    def mousePressEvent(self, event):
        """Override the mouse press event to handle selection."""
        if event.button() == Qt.LeftButton:
            self.selection_rect = QGraphicsRectItem(QRectF(event.pos(), event.pos()))
            self.selection_rect.setBrush(QBrush(QColor(0, 0, 255, 100)))  # Semi-transparent blue
            self.scene.addItem(self.selection_rect)
            self.selected_nodes.clear()  # Clear previous selection

    def mouseMoveEvent(self, event):
        """Override the mouse move event to update the selection rectangle."""
        if self.selection_rect is not None and event.buttons() & Qt.LeftButton:
            rect = QRectF(self.selection_rect.rect().topLeft(), event.pos())
            self.selection_rect.setRect(rect.normalized())
            self.update_selection()

    def mouseReleaseEvent(self, event):
        """Override the mouse release event to finalize selection."""
        if event.button() == Qt.LeftButton:
            self.update_selection()

    def update_selection(self):
        """Update the selection and highlight the nodes within the rectangle."""
        for node in self.nodes:
            if self.selection_rect.rect().intersects(node.sceneBoundingRect()):
                node.setBrush(QBrush(QColor(255, 255, 0)))  # Highlight selected nodes
                self.selected_nodes.append(node)
            else:
                node.setBrush(QBrush(QColor(200, 200, 255)))  # Reset color for non-selected nodes


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

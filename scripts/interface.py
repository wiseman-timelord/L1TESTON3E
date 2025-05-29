import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget, QHBoxLayout, QToolBar, QPushButton,
                             QComboBox, QFileDialog, QMessageBox, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import from utility and temporary
from utility import Node, save_tree_to_file, load_tree_from_file, import_cherrytree, add_node_to_tree, remove_node_from_tree, move_node_up, move_node_down, indent_node, outdent_node
from temporary import tree, selected_node, clipboard, clipboard_action, settings, load_settings, item_to_node

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiteStone")
        load_settings()
        self.resize(settings.get("window_width", 800), settings.get("window_height", 600))

        # Initialize global tree if not set
        global tree
        if tree is None:
            tree = Node("Root", "")

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Tree view
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Nodes")
        self.tree_widget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree_widget, 1)

        # Content display
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.update_node_content)
        self.text_edit.setFont(QFont(settings.get("default_font", "Arial"), settings.get("default_font_size", 12)))
        layout.addWidget(self.text_edit, 2)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open", self.open_file)
        file_menu.addAction("Save", self.save_file)
        file_menu.addAction("Options", lambda: QMessageBox.information(self, "Options", "Options not implemented yet"))

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        toolbar.addAction("Add Node", self.add_node)
        toolbar.addAction("Remove Node", self.remove_node)
        toolbar.addAction("Copy Node", self.copy_node)
        toolbar.addAction("Paste Node", self.paste_node)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New"])
        self.font_combo.setCurrentText(settings.get("default_font", "Arial"))
        self.font_combo.currentTextChanged.connect(self.change_font)
        toolbar.addWidget(self.font_combo)

        self.size_combo = QComboBox()
        self.size_combo.addItems(["10", "12", "14", "16", "18"])
        self.size_combo.setCurrentText(str(settings.get("default_font_size", 12)))
        self.size_combo.currentTextChanged.connect(self.change_font_size)
        toolbar.addWidget(self.size_combo)

        self.bold_button = QPushButton("B")
        self.bold_button.setCheckable(True)
        self.bold_button.clicked.connect(self.toggle_bold)
        toolbar.addWidget(self.bold_button)

        toolbar.addAction("Left", lambda: self.text_edit.setAlignment(Qt.AlignLeft))
        toolbar.addAction("Center", lambda: self.text_edit.setAlignment(Qt.AlignCenter))
        toolbar.addAction("Right", lambda: self.text_edit.setAlignment(Qt.AlignRight))

        self.refresh_tree()

    def refresh_tree(self):
        """Rebuild the tree widget while preserving the current selection."""
        global selected_node
        selected_path = self.get_node_path(selected_node) if selected_node else []
        self.tree_widget.clear()
        item_to_node.clear()

        def add_items(parent_item, node):
            item = QTreeWidgetItem(parent_item, [node.name])
            item_to_node[item] = node
            node.tree_item = item
            for child in node.children:
                add_items(item, child)

        root_item = QTreeWidgetItem(self.tree_widget, ["Root"])
        item_to_node[root_item] = tree
        tree.tree_item = root_item
        for child in tree.children:
            add_items(root_item, child)

        # Restore selection
        if selected_path:
            item = self.tree_widget.topLevelItem(0)
            for index in selected_path:
                if item and index < item.childCount():
                    item = item.child(index)
                else:
                    item = None
                    break
            if item:
                self.tree_widget.setCurrentItem(item)
                selected_node = item_to_node[item]
                self.text_edit.setHtml(selected_node.content)

    def get_node_path(self, node):
        """Return the path of a node as a list of indices from root."""
        path = []
        while node and node.parent:
            path.insert(0, node.parent.children.index(node))
            node = node.parent
        return path

    def on_item_selection_changed(self):
        """Update text edit with selected node's content."""
        global selected_node
        items = self.tree_widget.selectedItems()
        if items:
            selected_node = item_to_node[items[0]]
            self.text_edit.setHtml(selected_node.content)
        else:
            selected_node = None
            self.text_edit.clear()

    def on_item_changed(self, item, column):
        """Update node name after editing in tree widget."""
        if column == 0 and item in item_to_node:
            node = item_to_node[item]
            node.name = item.text(0)

    def update_node_content(self):
        """Update the content of the selected node."""
        if selected_node:
            html = self.text_edit.toHtml()
            if "data:image" in html and len(html) > 1024 * 1024:  # 1MB limit
                QMessageBox.warning(self, "Warning", "Large image detected. Consider resizing.")
            selected_node.content = html

    def open_context_menu(self, position):
        """Show context menu for right-clicked node."""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu()
            menu.addAction("Copy", self.copy_node)
            menu.addAction("Cut", self.cut_node)
            menu.addAction("Paste", self.paste_node)
            menu.addAction("Rename", self.rename_node)
            menu.addAction("Delete", self.delete_node)
            menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def keyPressEvent(self, event):
        """Handle node movement with Shift+Ctrl + arrow keys."""
        global selected_node
        if event.modifiers() == Qt.ShiftModifier | Qt.ControlModifier and selected_node:
            if event.key() == Qt.Key_Up:
                self.move_node_up()
            elif event.key() == Qt.Key_Down:
                self.move_node_down()
            elif event.key() == Qt.Key_Left:
                self.outdent_node()
            elif event.key() == Qt.Key_Right:
                self.indent_node()
        else:
            super().keyPressEvent(event)

    def save_file(self):
        """Prompt user to save the tree to a file."""
        global tree
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "LiteStone Files (*.lts)")
        if file_name:
            try:
                save_tree_to_file(tree, file_name)
                QMessageBox.information(self, "Success", "File saved successfully.")
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", "File not found.")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Corrupted file.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def open_file(self):
        """Prompt user to open a file and load the tree."""
        global tree, selected_node
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "LiteStone Files (*.lts);;CherryTree Files (*.ctd);;NoteCase Files (*.ncd)")
        if file_name:
            try:
                tree = load_tree_from_file(file_name)
                selected_node = None
                self.refresh_tree()
                QMessageBox.information(self, "Success", "File loaded successfully.")
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", "File not found.")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Corrupted file.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def add_node(self):
        """Add a new node to the tree."""
        global selected_node
        parent = selected_node if selected_node else tree
        add_node_to_tree(parent)
        self.refresh_tree()

    def remove_node(self):
        """Remove the selected node from the tree."""
        global selected_node
        if selected_node and selected_node.parent:
            remove_node_from_tree(selected_node)
            selected_node = None
            self.refresh_tree()

    def move_node_up(self):
        """Move the selected node up."""
        global selected_node
        if selected_node:
            move_node_up(selected_node)
            self.refresh_tree()

    def move_node_down(self):
        """Move the selected node down."""
        global selected_node
        if selected_node:
            move_node_down(selected_node)
            self.refresh_tree()

    def indent_node(self):
        """Indent the selected node."""
        global selected_node
        if selected_node:
            indent_node(selected_node)
            self.refresh_tree()

    def outdent_node(self):
        """Outdent the selected node."""
        global selected_node
        if selected_node:
            outdent_node(selected_node)
            self.refresh_tree()

    def copy_node(self):
        """Copy selected node to clipboard."""
        global selected_node, clipboard, clipboard_action
        if selected_node:
            clipboard = selected_node.copy()
            clipboard_action = "copy"

    def cut_node(self):
        """Cut selected node to clipboard."""
        global selected_node, clipboard, clipboard_action
        if selected_node and selected_node.parent:
            clipboard = selected_node.copy()
            clipboard_action = "cut"
            remove_node_from_tree(selected_node)
            selected_node = None
            self.refresh_tree()

    def paste_node(self):
        """Paste clipboard node under selected node or root."""
        global selected_node, clipboard, clipboard_action
        if clipboard:
            new_node = clipboard.copy()
            parent = selected_node if selected_node else tree
            parent.add_child(new_node)
            if clipboard_action == "cut":
                clipboard = None
                clipboard_action = None
            self.refresh_tree()

    def rename_node(self):
        """Start editing selected node's name."""
        global selected_node
        if selected_node:
            item = selected_node.tree_item
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.tree_widget.editItem(item)

    def delete_node(self):
        """Delete the selected node (except root)."""
        global selected_node
        if selected_node and selected_node.parent:
            remove_node_from_tree(selected_node)
            selected_node = None
            self.refresh_tree()
        else:
            QMessageBox.warning(self, "Warning", "Cannot delete the root node.")

    def change_font(self, font):
        """Change text font."""
        self.text_edit.setFontFamily(font)
        settings["default_font"] = font

    def change_font_size(self, size):
        """Change text font size."""
        self.text_edit.setFontPointSize(int(size))
        settings["default_font_size"] = int(size)

    def toggle_bold(self):
        """Toggle bold formatting."""
        self.text_edit.setFontWeight(QFont.Bold if self.bold_button.isChecked() else QFont.Normal)

    def closeEvent(self, event):
        """Save settings on close."""
        settings["window_width"] = self.width()
        settings["window_height"] = self.height()
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/persistent.json", "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save settings: {str(e)}")
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
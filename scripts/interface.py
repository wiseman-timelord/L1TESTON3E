import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget, QHBoxLayout, QToolBar, QPushButton,
                             QComboBox, QFileDialog, QMessageBox, QMenu, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
class DocumentTab(QWidget):\n    def __init__(self, document_root_node, main_window_ref, file_path=None):\n        super().__init__()\n        self.document_root_node = document_root_node\n        self.main_window_ref = main_window_ref\n        self.file_path = file_path\n        self.selected_node_in_tab = None\n        self.item_to_node_mapping = {}\n\n        layout = QHBoxLayout(self)\n\n        self.tree_widget = QTreeWidget()\n        self.tree_widget.setHeaderLabel("Nodes")\n        self.tree_widget.itemSelectionChanged.connect(self.on_tab_item_selection_changed)\n        self.tree_widget.itemChanged.connect(self.on_tab_item_changed)\n        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu) # For later use\n        # self.tree_widget.customContextMenuRequested.connect(self.open_tab_context_menu) # For later use\n        layout.addWidget(self.tree_widget, 1)\n\n        self.text_edit = QTextEdit()\n        self.text_edit.textChanged.connect(self.update_tab_node_content)\n        # Apply default font from settings (via main_window_ref or direct import of settings)\n        self.text_edit.setFont(QFont(settings.get("default_font", "Arial"), settings.get("default_font_size", 12)))\n        layout.addWidget(self.text_edit, 2)\n\n        self.setLayout(layout)\n        if self.document_root_node:\n            self.refresh_tree_widget()\n\n    def refresh_tree_widget(self):\n        current_selected_path = []\n        if self.selected_node_in_tab:\n            current_selected_path = self.get_node_path_in_tab(self.selected_node_in_tab)\n\n        self.tree_widget.clear()\n        self.item_to_node_mapping.clear()\n        if not self.document_root_node: return\n\n        def _add_items_recursive(parent_qt_item, parent_node_obj):\n            for child_node in parent_node_obj.children:\n                item = QTreeWidgetItem(parent_qt_item, [child_node.name])\n                item.setFlags(item.flags() | Qt.ItemIsEditable)\n                self.item_to_node_mapping[item] = child_node\n                child_node.tree_item = item \n                _add_items_recursive(item, child_node)\n\n        root_item_qt = QTreeWidgetItem(self.tree_widget, [self.document_root_node.name])\n        root_item_qt.setFlags(root_item_qt.flags() | Qt.ItemIsEditable)\n        self.item_to_node_mapping[root_item_qt] = self.document_root_node\n        self.document_root_node.tree_item = root_item_qt\n        _add_items_recursive(root_item_qt, self.document_root_node)\n        self.tree_widget.expandItem(root_item_qt)\n\n        if current_selected_path:\n            item_to_select = root_item_qt\n            # This path is relative to children of document_root_node if root is displayed\n            # Or relative to document_root_node's parent's children if root is not displayed.\n            # With current logic, path should be from the displayed root (document_root_node).\n            for index in current_selected_path:\n                if item_to_select and index < item_to_select.childCount():\n                    item_to_select = item_to_select.child(index)\n                else:\n                    item_to_select = None\n                    break\n            if item_to_select:\n                self.tree_widget.setCurrentItem(item_to_select)\n\n    def on_tab_item_selection_changed(self):\n        items = self.tree_widget.selectedItems()\n        if items:\n            node = self.item_to_node_mapping.get(items[0])\n            if node:\n                self.selected_node_in_tab = node\n                self.text_edit.setHtml(self.selected_node_in_tab.content)\n            else:\n                self.selected_node_in_tab = None # Should not happen ideally\n                self.text_edit.clear()\n        else:\n            self.selected_node_in_tab = None\n            self.text_edit.clear()\n\n    def on_tab_item_changed(self, item, column):\n        if column == 0:\n            node = self.item_to_node_mapping.get(item)\n            if node:\n                node.name = item.text(0)\n                if node == self.document_root_node and not self.file_path:\n                     self.main_window_ref.tab_widget.setTabText(self.main_window_ref.tab_widget.currentIndex(), node.name)\n\n    def update_tab_node_content(self):\n        if self.selected_node_in_tab:\n            self.selected_node_in_tab.content = self.text_edit.toHtml()\n\n    def get_node_path_in_tab(self, node):\n        path = []\n        current = node\n        while current and current.parent and current != self.document_root_node:\n            try:\n                path.insert(0, current.parent.children.index(current))\n            except ValueError:\n                path = [] # Should not happen in a consistent tree\n                break\n            current = current.parent\n        # If current is the document_root_node, the path is complete (it's a child of root or root itself)\n        # If current is None or current.parent is None before reaching root, path might be invalid.\n        # This logic assumes path is relative to children of document_root_node for selection purposes within refresh.\n        # However, if node is document_root_node, path should be empty.\n        if node == self.document_root_node:\n            return []\n        return path\n

# Import from utility and temporary
from utility import Node, save_tree_to_file, load_tree_from_file, import_cherrytree, add_node_to_tree, remove_node_from_tree, move_node_up, move_node_down, indent_node, outdent_node, save_tree_to_custom_format, load_tree_from_custom_format, merge_trees
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

# Tabbed layout
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)


        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open", self.open_file)
        file_menu.addAction("Save", self.save_file)
        file_menu.addAction("Save As...", self.save_file_as)
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


    def get_current_tab(self):\n        return self.tab_widget.currentWidget()\n\n    def close_tab(self, index):\n        widget = self.tab_widget.widget(index)\n        if widget is not None:\n            # TODO: Check for unsaved changes before closing\n            self.tab_widget.removeTab(index)\n            widget.deleteLater() # Important to clean up the widget\n

import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QHBoxLayout, QWidget, QToolBar, QPushButton, QComboBox, QFileDialog,
    QMessageBox, QMenu, QTabWidget, QInputDialog, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utility import (
    Node, save_tree_to_custom_format, load_tree_from_custom_format,
    import_cherrytree, add_node_to_tree, remove_node_from_tree,
    move_node_up, move_node_down, indent_node, outdent_node, merge_trees
)
from temporary import clipboard, clipboard_action, settings, load_settings

class DocumentTab(QWidget):
    """A tab containing a tree view and text editor for a single document."""
    def __init__(self, root_node, main_window):
        super().__init__()
        self.root_node = root_node  # Root node of the document's tree
        self.main_window = main_window
        self.selected_node = None  # Currently selected node in the tree
        self.item_to_node_map = {}  # Maps QTreeWidgetItems to Node objects
        self.file_path = None  # File path if the document is saved
        self.is_modified = False  # Tracks unsaved changes

        # Layout: tree on left, editor on right
        layout = QHBoxLayout(self)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Nodes")
        self.tree_widget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree_widget, 1)

        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.update_node_content)
        self.text_edit.setFont(QFont(settings.get("default_font", "Arial"), settings.get("default_font_size", 12)))
        layout.addWidget(self.text_edit, 2)
        self.setLayout(layout)
        self.refresh_tree_widget()

    def refresh_tree_widget(self):
        """Refresh the tree view to reflect the current node structure."""
        self.tree_widget.clear()
        self.item_to_node_map.clear()
        if self.root_node:
            root_item = QTreeWidgetItem(self.tree_widget, [self.root_node.name])
            root_item.setFlags(root_item.flags() | Qt.ItemIsEditable)
            self.item_to_node_map[root_item] = self.root_node
            self.root_node.tree_item = root_item
            self._add_child_items(root_item, self.root_node)
            self.tree_widget.expandItem(root_item)

    def _add_child_items(self, parent_item, parent_node):
        """Recursively populate the tree with child nodes."""
        for child in parent_node.children:
            child_item = QTreeWidgetItem(parent_item, [child.name])
            child_item.setFlags(child_item.flags() | Qt.ItemIsEditable)
            self.item_to_node_map[child_item] = child
            child.tree_item = child_item
            self._add_child_items(child_item, child)

    def on_item_selection_changed(self):
        """Update editor content when a tree node is selected."""
        items = self.tree_widget.selectedItems()
        if items:
            item = items[0]
            node = self.item_to_node_map.get(item)
            if node:
                self.selected_node = node
                self.text_edit.setHtml(node.content)
            else:
                self.selected_node = None
                self.text_edit.clear()
        else:
            self.selected_node = None
            self.text_edit.clear()

    def on_item_changed(self, item, column):
        """Update node name when edited in the tree."""
        if column == 0:
            node = self.item_to_node_map.get(item)
            if node:
                node.name = item.text(0)
                self.is_modified = True

    def update_node_content(self):
        """Update node content when the editor text changes."""
        if self.selected_node:
            self.selected_node.content = self.text_edit.toHtml()
            self.is_modified = True

    def open_context_menu(self, position):
        """Show context menu for tree nodes."""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu()
            menu.addAction("Copy", self.copy_node)
            menu.addAction("Cut", self.cut_node)
            menu.addAction("Paste", self.paste_node)
            menu.addAction("Rename", self.rename_node)
            menu.addAction("Delete", self.delete_node)
            menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def copy_node(self):
        """Copy the selected node to the clipboard."""
        global clipboard, clipboard_action
        if self.selected_node:
            clipboard = self.selected_node.copy()
            clipboard_action = "copy"

    def cut_node(self):
        """Cut the selected node to the clipboard."""
        global clipboard, clipboard_action
        if self.selected_node:
            clipboard = self.selected_node.copy()
            clipboard_action = "cut"
            remove_node_from_tree(self.selected_node)
            self.refresh_tree_widget()
            self.is_modified = True

    def paste_node(self):
        """Paste a node from the clipboard."""
        global clipboard, clipboard_action
        if clipboard and self.selected_node:
            new_node = clipboard.copy()
            self.selected_node.add_child(new_node)
            self.refresh_tree_widget()
            self.is_modified = True

    def rename_node(self):
        """Rename the selected node."""
        if self.selected_node:
            self.tree_widget.editItem(self.selected_node.tree_item)

    def delete_node(self):
        """Delete the selected node."""
        if self.selected_node:
            remove_node_from_tree(self.selected_node)
            self.refresh_tree_widget()
            self.selected_node = None
            self.text_edit.clear()
            self.is_modified = True

class OptionsDialog(QDialog):
    """Dialog for configuring application settings."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options")
        layout = QFormLayout(self)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New"])
        self.font_combo.setCurrentText(settings.get("default_font", "Arial"))
        layout.addRow("Default Font:", self.font_combo)
        self.size_combo = QComboBox()
        self.size_combo.addItems(["10", "12", "14", "16", "18"])
        self.size_combo.setCurrentText(str(settings.get("default_font_size", 12)))
        layout.addRow("Default Font Size:", self.size_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        """Apply settings when OK is clicked."""
        settings["default_font"] = self.font_combo.currentText()
        settings["default_font_size"] = int(self.size_combo.currentText())
        super().accept()

class MainWindow(QMainWindow):
    """Main window for the L1TESTON3E Tree-Document Editor."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiteStone")
        load_settings()
        self.resize(settings.get("window_width", 800), settings.get("window_height", 600))
        self.move(settings.get("window_x", 100), settings.get("window_y", 100))

        # Tabbed interface
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # File menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New", self.new_file, "Ctrl+N")
        file_menu.addAction("Open", self.open_file, "Ctrl+O")
        file_menu.addAction("Save", self.save_file, "Ctrl+S")
        file_menu.addAction("Save As...", self.save_file_as)
        file_menu.addAction("Merge Open Documents", self.merge_open_documents)
        file_menu.addAction("Merge from File", self.merge_from_file)
        file_menu.addAction("Options", self.open_options)
        file_menu.addAction("Quit", self.close, "Ctrl+Q")  # Closes immediately, no prompt

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
        toolbar.addAction("Left", lambda: self.set_text_alignment(Qt.AlignLeft))
        toolbar.addAction("Center", lambda: self.set_text_alignment(Qt.AlignCenter))
        toolbar.addAction("Right", lambda: self.set_text_alignment(Qt.AlignRight))

    def new_file(self):
        """Create a new blank document tab."""
        root_node = Node("New Node")  # Default root node name
        tab = DocumentTab(root_node, self)
        self.tab_widget.addTab(tab, "Untitled")
        self.tab_widget.setCurrentWidget(tab)

    def open_file(self):
        """Open an existing file in a new tab."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "LTS Files (*.lts);;CherryTree Files (*.ctd);;NoteCase Files (*.ncd)"
        )
        if file_path:
            try:
                if file_path.endswith(".lts"):
                    root_node = load_tree_from_custom_format(file_path)
                elif file_path.endswith(".ctd"):
                    root_node = import_cherrytree(file_path)
                elif file_path.endswith(".ncd"):
                    # Placeholder: assumes import_notecase exists in utility.py
                    raise NotImplementedError("NoteCase import not implemented yet")
                else:
                    raise ValueError("Unsupported file format.")
                tab = DocumentTab(root_node, self)
                tab.file_path = file_path
                self.tab_widget.addTab(tab, os.path.basename(file_path))
                self.tab_widget.setCurrentWidget(tab)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def save_file(self):
        """Save the current tab's document."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            if current_tab.file_path:
                try:
                    save_tree_to_custom_format(current_tab.root_node, current_tab.file_path)
                    current_tab.is_modified = False
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
            else:
                self.save_file_as()

    def save_file_as(self):
        """Save the current tab's document to a new file."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "LTS Files (*.lts)")
            if file_path:
                try:
                    save_tree_to_custom_format(current_tab.root_node, file_path)
                    current_tab.file_path = file_path
                    current_tab.is_modified = False
                    self.tab_widget.setTabText(self.tab_widget.indexOf(current_tab), os.path.basename(file_path))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def merge_open_documents(self):
        """Merge another open tab's content into the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab and self.tab_widget.count() > 1:
            tab_indices = [i for i in range(self.tab_widget.count()) if self.tab_widget.widget(i) != current_tab]
            tab_names = [self.tab_widget.tabText(i) for i in tab_indices]
            merge_tab_name, ok = QInputDialog.getItem(
                self, "Merge Documents", "Select document to merge:", tab_names, 0, False
            )
            if ok and merge_tab_name:
                merge_tab_index = tab_names.index(merge_tab_name)
                merge_tab = self.tab_widget.widget(tab_indices[merge_tab_index])
                merge_trees(current_tab.root_node, merge_tab.root_node)
                current_tab.refresh_tree_widget()
                current_tab.is_modified = True

    def merge_from_file(self):
        """Merge a file's content into the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Merge from File", "", "LTS Files (*.lts);;CherryTree Files (*.ctd);;NoteCase Files (*.ncd)"
            )
            if file_path:
                try:
                    if file_path.endswith(".lts"):
                        merge_root_node = load_tree_from_custom_format(file_path)
                    elif file_path.endswith(".ctd"):
                        merge_root_node = import_cherrytree(file_path)
                    elif file_path.endswith(".ncd"):
                        # Placeholder: assumes import_notecase exists
                        raise NotImplementedError("NoteCase import not implemented yet")
                    else:
                        raise ValueError("Unsupported file format.")
                    merge_trees(current_tab.root_node, merge_root_node)
                    current_tab.refresh_tree_widget()
                    current_tab.is_modified = True
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to merge file: {e}")

    def open_options(self):
        """Open the settings dialog."""
        dialog = OptionsDialog(self)
        if dialog.exec_():
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                tab.text_edit.setFont(QFont(settings.get("default_font", "Arial"), settings.get("default_font_size", 12)))

    def add_node(self):
        """Add a new node to the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab and current_tab.selected_node:
            new_node = add_node_to_tree(current_tab.selected_node)
            current_tab.refresh_tree_widget()
            if new_node.tree_item:
                current_tab.tree_widget.setCurrentItem(new_node.tree_item)
            current_tab.is_modified = True

    def remove_node(self):
        """Remove the selected node from the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab and current_tab.selected_node:
            remove_node_from_tree(current_tab.selected_node)
            current_tab.refresh_tree_widget()
            current_tab.selected_node = None
            current_tab.text_edit.clear()
            current_tab.is_modified = True

    def copy_node(self):
        """Copy the selected node in the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.copy_node()

    def paste_node(self):
        """Paste a node into the current tab."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.paste_node()

    def change_font(self, font_name):
        """Update the font in the current tab's editor."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.text_edit.setFontFamily(font_name)
            settings["default_font"] = font_name

    def change_font_size(self, size_str):
        """Update the font size in the current tab's editor."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            size = int(size_str)
            current_tab.text_edit.setFontPointSize(size)
            settings["default_font_size"] = size

    def toggle_bold(self):
        """Toggle bold formatting in the current tab's editor."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            font = current_tab.text_edit.currentFont()
            font.setBold(self.bold_button.isChecked())
            current_tab.text_edit.setCurrentFont(font)

    def set_text_alignment(self, alignment):
        """Set text alignment in the current tab's editor."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.text_edit.setAlignment(alignment)

    def close_tab(self, index):
        """Close a tab, prompting to save if modified."""
        widget = self.tab_widget.widget(index)
        if widget and widget.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        self.tab_widget.removeTab(index)
        widget.deleteLater()

    def keyPressEvent(self, event):
        """Handle node movement with Shift+Ctrl+Arrow keys."""
        if event.modifiers() == (Qt.ShiftModifier | Qt.ControlModifier):
            current_tab = self.tab_widget.currentWidget()
            if current_tab and current_tab.selected_node:
                if event.key() == Qt.Key_Up:
                    move_node_up(current_tab.selected_node)
                    current_tab.refresh_tree_widget()
                elif event.key() == Qt.Key_Down:
                    move_node_down(current_tab.selected_node)
                    current_tab.refresh_tree_widget()
                elif event.key() == Qt.Key_Left:
                    outdent_node(current_tab.selected_node)
                    current_tab.refresh_tree_widget()
                elif event.key() == Qt.Key_Right:
                    indent_node(current_tab.selected_node)
                    current_tab.refresh_tree_widget()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Save settings when the application closes."""
        settings["window_width"] = self.width()
        settings["window_height"] = self.height()
        settings["window_x"] = self.x()
        settings["window_y"] = self.y()
        with open("data/persistent.json", "w") as f:
            json.dump(settings, f, indent=2)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
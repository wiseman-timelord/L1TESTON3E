import json
import xml.etree.ElementTree as ET
import sqlite3
from copy import deepcopy

# Assuming Node class is already defined in utility.py
class Node:
    def __init__(self, name, content="", parent=None):
        self.name = name
        self.content = content
        self.parent = parent
        self.children = []
        self.tree_item = None  # Reference to QTreeWidgetItem

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(data["name"], data.get("content", ""))
        for child_data in data.get("children", []):
            node.add_child(cls.from_dict(child_data))
        return node

    def copy(self):
        return deepcopy(self)

# Existing import functions (assumed from original utility.py)
def import_cherrytree(file_name):
    # Placeholder implementation (replace with actual logic)
    tree = Node("Imported Root", "")
    # Add logic to parse .ctd file and build tree
    return tree

def import_notecase(file_name):
    # Placeholder implementation (replace with actual logic)
    tree = Node("Imported Root", "")
    # Add logic to parse .ncd file and build tree
    return tree

# File operation functions moved from interface.py
def save_tree_to_file(tree, file_name):
    """Save the tree structure to a .lts file."""
    if not file_name.endswith(".lts"):
        file_name += ".lts"
    with open(file_name, "w") as f:
        json.dump(tree.to_dict(), f, indent=2)

def load_tree_from_file(file_name):
    """Load a tree structure from a file (.lts, .ctd, or .ncd)."""
    if file_name.endswith(".lts"):
        with open(file_name, "r") as f:
            data = json.load(f)
            return Node.from_dict(data)
    elif file_name.endswith(".ctd"):
        return import_cherrytree(file_name)
    elif file_name.endswith(".ncd"):
        return import_notecase(file_name)
    else:
        raise ValueError("Unsupported file format.")

# Tree manipulation functions moved from interface.py
def add_node_to_tree(parent_node, name="New Node", content=""):
    """Add a new node to the tree under the specified parent."""
    new_node = Node(name, content)
    parent_node.add_child(new_node)
    return new_node

def remove_node_from_tree(node):
    """Remove a node from its parent's children."""
    if node.parent:
        node.parent.remove_child(node)

def move_node_up(node):
    """Move a node up among its siblings."""
    if node.parent:
        index = node.parent.children.index(node)
        if index > 0:
            node.parent.children[index], node.parent.children[index - 1] = \
                node.parent.children[index - 1], node.parent.children[index]

def move_node_down(node):
    """Move a node down among its siblings."""
    if node.parent:
        index = node.parent.children.index(node)
        if index < len(node.parent.children) - 1:
            node.parent.children[index], node.parent.children[index + 1] = \
                node.parent.children[index + 1], node.parent.children[index]

def indent_node(node):
    """Indent a node to become a child of its previous sibling."""
    if node.parent:
        index = node.parent.children.index(node)
        if index > 0:
            prev_sibling = node.parent.children[index - 1]
            node.parent.children.remove(node)
            prev_sibling.add_child(node)

def outdent_node(node):
    """Outdent a node to its parent's level."""
    if node.parent and node.parent.parent:
        current_parent = node.parent
        grandparent = current_parent.parent
        index = grandparent.children.index(current_parent) + 1
        current_parent.remove_child(node)
        grandparent.children.insert(index, node)
        node.parent = grandparent
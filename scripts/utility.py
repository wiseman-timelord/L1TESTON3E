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

# --- Helper functions for custom binary format ---
def _write_length_prefixed_string(f, text_string):
    """Encodes a string to UTF-8, writes its length (4 bytes, big-endian), then writes the string bytes."""
    encoded_bytes = text_string.encode('utf-8')
    f.write(len(encoded_bytes).to_bytes(4, 'big'))
    f.write(encoded_bytes)

def _read_length_prefixed_string(f, field_name_for_error="string"):
    """Reads a 4-byte length (big-endian), then reads that many bytes and decodes from UTF-8."""
    len_bytes = f.read(4)
    if not len_bytes or len(len_bytes) < 4: # Check for EOF or incomplete length
        raise ValueError(f"Invalid LTS file format: unexpected EOF while reading {field_name_for_error} length")
    
    string_len = int.from_bytes(len_bytes, 'big')
    
    string_bytes = f.read(string_len)
    if len(string_bytes) != string_len: # Check for EOF or incomplete data
        raise ValueError(f"Invalid LTS file format: unexpected EOF while reading {field_name_for_error} data (expected {string_len} bytes, got {len(string_bytes)})")
    
    return string_bytes.decode('utf-8')
# --- End Helper functions ---

# LTS format functions
def save_tree_to_custom_format(tree, file_name):
    if not file_name.endswith(".lts"):
        file_name += ".lts"
    try:
        with open(file_name, "wb") as f:
            f.write(b'LTS1') # Magic number
            _write_node_recursive(f, tree)
    except IOError as e:
        raise IOError(f"Error saving to LTS file '{file_name}': {e}")

def _write_node_recursive(f, node_to_write):
    _write_length_prefixed_string(f, node_to_write.name)
    _write_length_prefixed_string(f, node_to_write.content)
    
    f.write(len(node_to_write.children).to_bytes(4, 'big'))
    for child in node_to_write.children:
        _write_node_recursive(f, child)

def load_tree_from_custom_format(file_name):
    try:
        with open(file_name, "rb") as f:
            magic_number = f.read(4)
            if magic_number != b'LTS1':
                raise ValueError("Invalid LTS file format: incorrect magic number")
            return _read_node_recursive(f)
    except IOError as e:
        raise IOError(f"Error loading from LTS file '{file_name}': {e}")
    # ValueError from _read_node_recursive or magic number check will propagate

def _read_node_recursive(f):
    name = _read_length_prefixed_string(f, "node name")
    content = _read_length_prefixed_string(f, "node content")

    current_node = Node(name, content)

    num_children_bytes = f.read(4)
    if not num_children_bytes or len(num_children_bytes) < 4: # Check for EOF
        raise ValueError("Invalid LTS file format: unexpected EOF while reading number of children")
    num_children = int.from_bytes(num_children_bytes, 'big')

    for _ in range(num_children):
        child_node = _read_node_recursive(f)
        current_node.add_child(child_node)
    
    return current_node

# CherryTree Importer
def import_cherrytree(file_name):
    """Imports a CherryTree document (.ctd) into the application's Node structure."""
    try:
        xml_tree = ET.parse(file_name)
        xml_root = xml_tree.getroot() 
    except FileNotFoundError:
        raise FileNotFoundError(f"CherryTree file not found: {file_name}")
    except ET.ParseError:
        raise ValueError(f"Invalid XML in CherryTree file: {file_name}")

    app_root_node = Node("Imported CherryTree") 

    def _parse_xml_node(xml_node_element, parent_app_node):
        name = xml_node_element.get("name", "Untitled")
        rich_text_content = xml_node_element.get("rich_text", "")
        if not rich_text_content:
             rich_text_element = xml_node_element.find('rich_text')
             if rich_text_element is not None and rich_text_element.text:
                 rich_text_content = rich_text_element.text
        app_node = Node(name, rich_text_content)
        if parent_app_node:
            parent_app_node.add_child(app_node)
        for child_xml_element in xml_node_element.findall('node'):
            _parse_xml_node(child_xml_element, app_node)
        return app_node

    for child_xml_node in xml_root.findall('node'):
        _parse_xml_node(child_xml_node, app_root_node)
    return app_root_node

# NoteCase Importer
def import_notecase(file_name):
    """Imports a NoteCase document (.ncd) into the application's Node structure."""
    conn = None
    try:
        # Attempt to connect to the database file
        try:
            conn = sqlite3.connect(f"file:{file_name}?mode=ro", uri=True) # Open in read-only mode
        except sqlite3.OperationalError as e:
            # This can happen if the file doesn't exist, isn't a SQLite DB, or permissions are wrong
            raise ValueError(f"Failed to open NoteCase file '{file_name}'. It might be missing, corrupted, or not a valid SQLite database. Original error: {e}")

        cursor = conn.cursor()
        
        # Try to query with html_content first
        try:
            cursor.execute("SELECT id, parent_id, title, html_content FROM nodes ORDER BY parent_id, id")
            all_rows = cursor.fetchall()
        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT id, parent_id, title, rtf_content FROM nodes ORDER BY parent_id, id")
                all_rows = cursor.fetchall()
            except sqlite3.OperationalError as e_html_err:
                # If html_content fails, try rtf_content
                try:
                    cursor.execute("SELECT id, parent_id, title, rtf_content FROM nodes ORDER BY parent_id, id")
                    all_rows = cursor.fetchall()
                except sqlite3.OperationalError as e_rtf_err:
                    raise ValueError(f"Could not find expected 'nodes' table or required columns (tried html_content and rtf_content) in NoteCase DB '{file_name}'. Errors: HTML attempt -> {e_html_err}, RTF attempt -> {e_rtf_err}")
        
        app_root_node = Node("Imported NoteCase") # Root node for the imported structure
        db_nodes_map = {} # To quickly access nodes by their DB ID
        raw_node_data = [] # Store (id, parent_id) tuples for hierarchy reconstruction

        # First pass: create all Node objects and store them in db_nodes_map
        for row in all_rows:
            node_id, parent_id, title, content_data = row[0], row[1], row[2], row[3]
            
            # Ensure title is a string, default to "Untitled" if None or empty
            title_str = title if title else "Untitled"
            
            # Ensure content is a string, default to empty string if None
            content_str = str(content_data) if content_data is not None else ""
            
            app_node = Node(name=title_str, content=content_str)
            db_nodes_map[node_id] = app_node
            raw_node_data.append({'id': node_id, 'parent_id': parent_id, 'node_obj': app_node})

        # Second pass: build the hierarchy
        for data in raw_node_data:
            app_node = data['node_obj']
            parent_id = data['parent_id']
            
            if parent_id is not None and parent_id in db_nodes_map:
                parent_app_node = db_nodes_map[parent_id]
                parent_app_node.add_child(app_node)
            else:
                # Node is a root (or orphaned, becomes a root under our main import node)
                app_root_node.add_child(app_node)
        
        return app_root_node

    # Removed FileNotFoundError catch as the initial sqlite3.connect(uri=True) handles it better by raising OperationalError.
    except sqlite3.Error as e: 
        # This will catch errors like "file is not a database" if not caught by the more specific OperationalError above,
        # or other general SQLite errors during query execution if not caught by inner blocks.
        raise ValueError(f"SQLite database error with NoteCase file '{file_name}': {e}")
    except ValueError as e: # Re-raise ValueErrors from specific checks
        raise e
    except Exception as e: 
        # Catch any other unexpected errors during the process
        raise RuntimeError(f"An unexpected error occurred during NoteCase import of '{file_name}': {e}")
    finally:
        if conn:
            conn.close()

# File operation functions
def load_tree_from_file(file_name):
    if file_name.endswith(".lts"):
        # Attempt to load directly using the custom binary format.
        # Errors from load_tree_from_custom_format (IOError, ValueError for format issues)
        # will propagate up as per requirements.
        return load_tree_from_custom_format(file_name)
    elif file_name.endswith(".ctd"):
        return import_cherrytree(file_name)
    elif file_name.endswith(".ncd"):
        return import_notecase(file_name)
    else:
        raise ValueError("Unsupported file format.")

# Tree manipulation functions
def add_node_to_tree(parent_node, name="New Node", content=""):
    if not isinstance(parent_node, Node):
        raise TypeError("parent_node must be an instance of Node")
    new_node = Node(name, content)
    parent_node.add_child(new_node)
    return new_node

def remove_node_from_tree(node):
    if not isinstance(node, Node):
        raise TypeError("node must be an instance of Node")
    if node.parent: 
        node.parent.remove_child(node)

def move_node_up(node):
    if not isinstance(node, Node):
        raise TypeError("node must be an instance of Node")
    if node.parent:
        try:
            index = node.parent.children.index(node)
            if index > 0:
                node.parent.children[index], node.parent.children[index - 1] = \
                    node.parent.children[index - 1], node.parent.children[index]
        except ValueError: 
            pass 

def move_node_down(node):
    if not isinstance(node, Node):
        raise TypeError("node must be an instance of Node")
    if node.parent:
        try:
            index = node.parent.children.index(node)
            if index < len(node.parent.children) - 1:
                node.parent.children[index], node.parent.children[index + 1] = \
                    node.parent.children[index + 1], node.parent.children[index]
        except ValueError:
            pass

def indent_node(node):
    if not isinstance(node, Node):
        raise TypeError("node must be an instance of Node")
    if node.parent:
        try:
            index = node.parent.children.index(node)
            if index > 0:
                prev_sibling = node.parent.children[index - 1]
                node.parent.remove_child(node) 
                prev_sibling.add_child(node)    
        except ValueError:
            pass

def outdent_node(node):
    if not isinstance(node, Node):
        raise TypeError("node must be an instance of Node")
    if node.parent and node.parent.parent:
        current_parent = node.parent
        grandparent = current_parent.parent
        try:
            parent_index_in_grandparent = grandparent.children.index(current_parent)
            current_parent.remove_child(node) 
            grandparent.children.insert(parent_index_in_grandparent + 1, node)
            node.parent = grandparent 
        except ValueError: 
            pass

def merge_trees(base_tree_root, tree_to_merge_root):
    if not isinstance(base_tree_root, Node) or not isinstance(tree_to_merge_root, Node):
        raise TypeError("Both arguments must be Node instances")
    for child_node in tree_to_merge_root.children:
        base_tree_root.add_child(child_node.copy())

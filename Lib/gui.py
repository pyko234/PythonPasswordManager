import tkinter as tk
from tkinter import ttk, font
from Lib import db_manager
import secrets


class SplashScreen:
    def __init__(self, root):
        # Initialize the splash screen with the provided root window
        self.root = root
        self.root.title("Splash Screen")
        self.password = ''
        self.create_widgets()

    def create_widgets(self):
        # Create the widgets for the splash screen

        # Define the text to be displayed in the splash screen
        text = """
        This is the splash screen for first time run.

        Before we can get started, you need to enter a password
        that will be used to encrypt stored passwords and when hashed
        will allow you access to this application.

        You do not have to hash the password the script does it automatically."""

        # Create a label to display the introductory text
        intro_label = ttk.Label(self.root, text=text)
        intro_label.pack(pady=50)

        # Create a label for the password input field
        password_label = ttk.Label(self.root, text='Password:')
        password_label.pack(pady=5)

        # Create an entry widget for entering the password
        password_entry = ttk.Entry(self.root)
        password_entry.pack(pady=5)

        # Create a button to indicate completion and bind it to the return_password method
        finished_button = ttk.Button(self.root, text='Completed', command=lambda: self.return_password(password_entry))
        finished_button.pack(pady=10)

        # Bind the Enter key press event to the return_password method
        password_entry.bind("<Return>", lambda event: self.return_password(password_entry))

    def return_password(self, entry):
        # Retrieve the entered password and destroy the splash screen window
        self.password = entry.get()
        self.root.destroy()


class AddAndEditScreen:
    def __init__(self, root, username, password):
        self.root = root
        self.root.title("Add/Edit Password")
        self.username = username
        self.password = password
        self.create_widgets()

    def create_widgets(self):
        # Create label and entry frames for organizing the widgets
        label_frame = tk.Frame(self.root)
        entry_frame = tk.Frame(self.root)

        label_frame.grid(row=0, column=0, padx=5)
        entry_frame.grid(row=0, column=1, padx=5)

        # Create labels for username and password
        username_label = tk.Label(label_frame, text="Username: ")
        password_label = tk.Label(label_frame, text="Password: ")

        # Pack the labels in the label frame
        username_label.pack(pady=5)
        password_label.pack(pady=5)

        # Create entry fields for username and password
        username_entry = tk.Entry(entry_frame)
        password_entry = tk.Entry(entry_frame)

        # Insert the initial values for username and password
        username_entry.insert(0, self.username)
        password_entry.insert(0, self.password)

        # Pack the entry fields in the entry frame
        username_entry.pack(pady=5)
        password_entry.pack(pady=5)

        # Create a "Generate Password" button
        gen_button = tk.Button(self.root, text="Generate Password",
                               command=lambda: self.generate_password(password_entry))
        gen_button.grid(row=0, column=2, pady=10, padx=5)

        # Create a "Finished" button
        finished_button = tk.Button(self.root, text="Finished",
                                    command=lambda: self.finished([username_entry.get(), password_entry.get()]))
        finished_button.grid(row=1, column=1, pady=10)

    def finished(self, data):
        # Update the username and password values
        self.username = data[0]
        self.password = data[1]
        self.root.destroy()

    @staticmethod
    def generate_password(entry):
        # Generate a new password using the db_manager
        password = db_manager.generate_password()

        # Clear the entry field and insert the generated password
        entry.delete(0, tk.END)
        entry.insert(0, password)



class MainGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Password Manager")
        self.create_widgets()

    def create_widgets(self):
        # Create a label for usernames
        label = ttk.Label(self.root, text="Usernames:")
        label.pack(pady=10)

        # Create a frame for the treeview
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(pady=10)

        # Create a treeview with ID and Username columns
        tree = ttk.Treeview(tree_frame, columns=("ID", "Username"), show="headings")
        tree.pack(side='left')

        # Create a vertical scrollbar for the treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Set the headings for the treeview
        tree.heading("ID", text="ID")
        tree.heading("Username", text="Username")

        # Fill the treeview with data
        self.fill_tree(tree)

        # Create an "Edit Selection" button
        edit_button = tk.Button(self.root, text="Edit Selection", command=lambda: self.edit_tree(tree))
        edit_button.pack(pady=5)

        # Create an "Add New Entry" button
        add_button = tk.Button(self.root, text="Add New Entry", command=lambda: self.add_item(tree))
        add_button.pack(pady=5)

    def add_item(self, tree):
        # Create a new window for adding an item
        window = tk.Tk()
        add_window = AddAndEditScreen(window, '', '')
        window.wait_window(add_window.root)

        # Generate a new initialization vector (iv) and encryption key
        iv = secrets.token_bytes(16)
        key = db_manager.generate_encryption_key(iv)

        # Encrypt the password using the new key and iv
        encrypted_password = db_manager.encrypt_password(add_window.password, key, iv)

        # Add the new data to the database
        db_manager.add_data_to_db([add_window.username, encrypted_password, key, iv])

        # Refresh the tree to reflect the changes
        self.refresh_tree(tree)

    @staticmethod
    def fill_tree(tree):
        # Get the data from the database
        data = db_manager.view_database()

        # Insert each row of data into the treeview
        for x in data:
            tree.insert("", "end", values=(x[0], x[1]))

        # Configure the column widths
        tree.column("ID", anchor="center")
        tree_font = ("", 12)
        tree.column("ID", width=tk.font.Font(font=tree_font).measure("9999"))

        for item in tree.get_children():
            values = tree.item(item)["values"]
            for i in range(len(values)):
                column_width = font.Font(font=tree_font).measure(values[i])
                if tree.column(tree["columns"][i], width=None) < column_width:
                    tree.column(tree["columns"][i], width=column_width)

    def edit_tree(self, tree):
        # Retrieve the selected item from the tree
        selected_item = tree.selection()
        if selected_item:
            # Get the values of the selected item
            item_values = tree.item(selected_item)["values"]

            # Retrieve the data from the database using the item values
            data = db_manager.pull_data_from_user(item_values[1])

            # Decrypt the password retrieved from the database
            decrypted_password = db_manager.decrypt_password(data[2], data[3], data[4])

            # Create a new window for editing the item
            window = tk.Tk()
            edit_window = AddAndEditScreen(window, data[1], decrypted_password)
            window.wait_window(edit_window.root)

            # Generate a new initialization vector (iv) and encryption key
            iv = secrets.token_bytes(16)
            key = db_manager.generate_encryption_key(iv)

            # Encrypt the edited password using the new key and iv
            encrypted_password = db_manager.encrypt_password(edit_window.password, key, iv)

            # Update the data in the database with the edited values
            db_manager.edit_data_in_db([data[0], edit_window.username, encrypted_password, key, iv])

            # Refresh the tree to reflect the changes
            self.refresh_tree(tree)

    def refresh_tree(self, tree):
        # Delete all children from the tree
        children = tree.get_children()
        for child in children:
            tree.delete(child)

        # Fill the tree with updated data
        self.fill_tree(tree)


from Lib import db_manager, gui
import tkinter as tk
import secrets


def add_test_data():

    for i in range(10):

        # Generate random value for encryption
        iv = secrets.token_bytes(16)

        # Generate key using random value
        key = db_manager.generate_encryption_key(iv)
        string = f"string{i}"

        # Encrypt string and add it do the Database
        db_manager.add_data_to_db([f"string{i}", db_manager.encrypt_password(string, key, iv), key, iv])

def main():

    # Create window
    root = tk.Tk()

    # Add frame to window
    main_gui = gui.MainGui(root)

    # Run mainloop from window
    root.mainloop()


if __name__ == '__main__':
    main()

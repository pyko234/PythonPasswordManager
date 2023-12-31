import os
import sqlite3
import sys
import tkinter as tk
import string
import random

from pathlib import Path
from tkinter import simpledialog, messagebox

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from Lib import gui

# All logic to be done in main. This file to manage the database to store passwords securely

# Password hashing parameters
SALT_SIZE = 32
KEY_SIZE = 32
ITERATIONS = 100000


# This function to check for OS
def check_os():
    # this call dumps os
    platform = sys.platform

    # This adjusts the default install location for files based on platform
    if platform.startswith('win'):
        install_location = Path(f"{Path.home()}/PythonPasswordManager")
    elif platform.startswith('linux'):
        home_dir = os.path.expanduser('~')
        install_location = Path(os.path.join(home_dir, 'PythonPasswordManager'))
    elif platform.startswith('darwin'):
        install_location = Path('/Applications/PythonPasswordManager')
    else:
        install_location = None

    # If there is no folder, create it
    if not install_location.is_dir():
        try:
            install_location.mkdir(parents=True)
            messagebox.showinfo(title=None, message=f"Folder 'PythonPasswordManager' created at: {install_location}")

        except FileExistsError:
            # Handle scenario when the folder already exists
            messagebox.showwarning(title=None,
                                   message=f"Folder 'PythonPasswordManager' already exists at: {install_location}")

        except Exception as e:
            # Handle other exceptions during folder creation
            messagebox.showerror(title=None, message=f"Error occurred while creating the folder: {e}")

    return install_location


# This function to check for first time run
def check_for_first_time(path):
    # Create a Path object for the database file
    path_obj = Path(f'{path}/Database.db')

    # Check if the database file exists
    if not path_obj.is_file():
        # If the database file doesn't exist, generate the database
        generate_database(path)

    # Connect to the database
    conn, cursor = connect_to_database(path)

    # Execute a SELECT query to retrieve all data from the passwords table
    cursor.execute("SELECT * FROM master")

    # Fetch all rows from the result set
    data = cursor.fetchall()

    # Check if there are no records in the passwords table
    if len(data) == 0:
        # If there are no records, display the splash screen
        root = tk.Tk()
        splash = gui.SplashScreen(root)
        root.mainloop()

        # Retrieve the password from the splash screen
        password = splash.password

        # Encrypt the password
        hashed_password = encrypt_master_password(password)

        # Add the encrypted password to the database
        cursor.execute("INSERT INTO master (password) VALUES (?)", (hashed_password,))
        conn.commit()


def login():
    # Connect to the database
    conn, cursor = connect_to_database(path=location)

    # Ask for the password using a dialog box
    password = simpledialog.askstring("Login", "Please enter password:")

    # Encrypt the entered password
    hashed_password = encrypt_master_password(password)

    # Retrieve the stored password from the database
    cursor.execute("SELECT * FROM master")
    stored_password = cursor.fetchone()[0]

    # Compare the entered password with the stored password
    if hashed_password != stored_password:
        # Show an error message if the passwords do not match
        messagebox.showerror(title=None, message="Password does not match stored password!\nExiting Program")
        sys.exit()

    # Return the entered password
    return password


# This function to take password and salt and generate encrypted password
def encrypt_master_password(password):
    # Fixed salt value
    salt = b'\x8dm\x8a\x13\xe5R\xa1\xbc{(\xd9qO\x9d\xefC'

    # Key derivation using PBKDF2 with SHA256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )

    # Use the derived key
    key = kdf.derive(password.encode())

    return salt + key


# This function to Generate an encryption key from the global password and a random value
def generate_encryption_key(random_value):
    # Perform key derivation using PBKDF2 with SHA256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=global_password.encode(),
        iterations=100000
    )

    # Use the derived key up to 32 bytes
    key = kdf.derive(random_value)[:32]

    return key


# This function is to encrypt data
def encrypt_password(password, encryption_key, iv):
    # Create a Cipher object with AES algorithm and CBC mode
    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))

    # Create an encryptor object from the cipher
    encryptor = cipher.encryptor()

    # Create a PKCS7 padding object with a block size of 128 bits
    padder = padding.PKCS7(128).padder()

    # Pad the password string
    padded_data = padder.update(password.encode()) + padder.finalize()

    # Perform the encryption process
    encrypted_password = encryptor.update(padded_data) + encryptor.finalize()

    return encrypted_password


# This function to decrypt encrypted data
def decrypt_password(encrypted_password, iv):
    # Generate key using global password and salt from DB
    encryption_key = generate_encryption_key(iv)

    # Create a Cipher object with AES algorithm and CBC mode
    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))

    # Create a decryptor object from the cipher
    decryptor = cipher.decryptor()

    # Perform the decryption process
    decrypted_data = decryptor.update(encrypted_password) + decryptor.finalize()

    # Create a PKCS7 padding object with a block size of 128 bits
    unpadder = padding.PKCS7(128).unpadder()

    # Remove the padding from the decrypted data
    unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

    # Return the decrypted and unpadded data as a string
    return unpadded_data.decode()


# This function to generate a database, to be called if none exist
def generate_database(path):
    # Create Database file
    file_path = path / "Database.db"
    file = open(file_path, "w")
    file.close()

    # Connect to database
    conn = sqlite3.connect(path / "Database.db")

    # Create Cursor to execute sql
    cursor = conn.cursor()

    # Create SQL query to generate table
    sql = """CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            iv TEXT NOT NULL
        )"""

    # Use cursor to execute the sql query
    cursor.execute(sql)

    # Generate master table
    sql = """CREATE TABLE IF NOT EXISTS master (
    password TEXT NOT NULL
    )"""

    # Use cursor to execute
    cursor.execute(sql)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


# This function to connect to database and return conn and cursor
def connect_to_database(path):
    # Create connection using sqlite3
    conn = sqlite3.connect(path / "Database.db")

    # Generate cursor
    cursor = conn.cursor()

    # Return both objects
    return conn, cursor


# This function for viewing the database
def view_database():
    # Call function to get conn and cursor objects
    conn, cursor = connect_to_database(path=location)

    # Execute query to view all entries in database
    cursor.execute("""SELECT * FROM passwords""")

    # Get data from cursor
    data = cursor.fetchall()

    # Return the output
    return data


# This function to pull data from db by user
def pull_data_from_user(username):
    # Get conn and cursor objects
    conn, cursor = connect_to_database(path=location)

    # Execute SQL Query to find data by username
    cursor.execute(f"SELECT * FROM passwords WHERE username = '{username}'")

    # Load data into variable
    data = cursor.fetchone()

    # Return data
    return data


# This function to add data to database
def add_data_to_db(data):
    # Get connection and cursor to database
    conn, cursor = connect_to_database(path=location)

    # Insert data into table
    cursor.execute("INSERT INTO passwords (username, password, iv) VALUES (?, ?, ?)", data)

    # Commit changes to database
    conn.commit()


# This function to edit data in table
def edit_data_in_db(data):
    # Get connection and cursor objetcs
    conn, cursor = connect_to_database(path=location)

    # Generate SQL qurey to update data
    sql = f"UPDATE passwords SET username = ?, password = ?, iv = ? WHERE id = {data[0]}"

    # Execute the command
    cursor.execute(sql, data[1::])

    # Commit changes
    conn.commit()


# This function generates a random password, by default will be 12 characters
def generate_password():
    # Get list of avaiable characters
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate the password
    password = ''.join(random.choice(characters) for _ in range(12))

    # Return Generated password
    return password


# This to determine the OS and set library wide variables while library in use
location = check_os()
check_for_first_time(location)
global_password = login()

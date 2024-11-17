import socket
from _thread import *
import threading
import fnmatch
import sqlite3
import json
import os

BUFFER_SIZE = 1024
print_lock = threading.Lock()
BASE_DIR = ""
DB_NAME = "filesystem.db"


def download(conn, filename, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        cursor.execute("SELECT fileData FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))
        file_data = cursor.fetchone()
        cursor.close()

        print(file_data)
        if file_data is None or file_data[0] is None:
            message = f"File: {filename} is not found"
            send_response(conn, 400, message)
            return

        send_response(conn, 200, data=file_data[0])
        print(f"Sent file: {filename} to client")

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        print(f"Error accessing the database: {e}")
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        print(f"Unexpected error: {e}")
        return


def upload(conn, filename, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM Directories WHERE name = ?", (cwd,))

        if not cursor.fetchone():
            message = f"Directory: {cwd} does not exist"
            send_response(conn, 400, message)
            return
        send_response(conn, 200)
    
        print("Receiving file...")

        fileData = b""
        while True:
            data = conn.recv(BUFFER_SIZE)
            if b"EOF" in data:  # End-of-file marker
                fileData += data.replace(b"EOF", b"")
                break
            fileData += data

        # with open(f"f_{filename}", 'wb') as file:
        #     while True:
        #         data = conn.recv(BUFFER_SIZE)
        #         if b'EOF' in data:  # Check for the end marker
        #             file.write(data.replace(b'EOF', b''))  # Remove the marker
        #             break
        #         file.write(data)

        print(f"File: '{filename}' received")

        # with open(f"f_{filename}", 'rb') as f:
        #     data = f.read()

        type = get_file_type(filename)
        size = len(fileData)
        cursor.execute("INSERT INTO Files (fileName, fileParent, fileType, fileBytes, fileData) VALUES (?, ?, ?, ?, ?)", (filename, cwd, type, size, fileData))
        db.commit()
        db.close()

        message = f"File: {filename} sucessfully uploaded"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        print(f"Error accessing the database: {e}")
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        print(f"Unexpected error: {e}")
        return


def cd(conn, cwd, new_dir):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    # make sure the dir exists, then return it
    cursor.execute("SELECT name FROM Directories WHERE parent = ?", (cwd,))
    if not cursor.fetchone():
        conn.send(f"Directory: {cwd} does not exist")
        return
    
    if new_dir in cursor.fetchall():
        conn.send(new_dir)
        conn.send(f"cd sucessful to: {new_dir}")


def setup_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Directories (
    name TEXT NOT NULL,
    parent TEXT NOT NULL,
    PRIMARY KEY (name, parent)
    FOREIGN KEY (parent) REFERENCES Directories(name) ON DELETE CASCADE
    );
    ''')

    cursor.execute('''INSERT OR IGNORE INTO Directories(name, parent) VALUES ("home", "home");''')

    cursor.execute('''SELECT * FROM Files WHERE fileParent = "home";''')
    print(cursor.fetchall())

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Files (
    fileName TEXT NOT NULL,
    fileParent TEXT NOT NULL,
    fileType TEXT NOT NULL,
    fileBytes FLOAT NOT NULL,
    fileData BLOB NOT NULL,
    PRIMARY KEY (fileName, fileParent)
    FOREIGN KEY (fileParent) REFERENCES Directories(name) ON DELETE CASCADE
    );
    ''')

    conn.commit()
    conn.close()


def get_file_type(filename):
    extension = filename.split('.', 1)[1]

    audio = ["mp3", "wav"]
    text = ["txt", "cpp", "py", "md"]
    image = [".jpg", "png"]
    video = ["mp4", "avi"]

    if extension in audio:
        return "audio"
    elif extension in text:
        return "text"
    elif extension in image:
        return "image"
    elif extension in video:
        return "video"
    else:
        return "unknown"
    

def send_response(conn, status, message = None, data = None):
    response = {
        "status": status,
        "message": message,
        "data": data
    }

    conn.send(json.dumps(response).encode())


def threaded_server(conn):
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(BUFFER_SIZE).decode()
        if not data:
            # if data is not received break
            break
        
        args = data.split()

        match args[0]:
            case "cd":
                cd(conn, args[1], args[2]) #cd cwd newdir
            case "upload":
                upload(conn, args[1], args[2]) # upload filename cwd
            case "quit":
                break
        #send_response(....?)

    conn.close()  # close the connection


def run_server():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    setup_db()


    server_socket = socket.socket() 

    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(5)

    while True:
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        start_new_thread(threaded_server, (conn,))

    conn.close()  
    
if __name__ == '__main__':
    run_server()

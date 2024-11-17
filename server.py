import socket
from _thread import *
import threading
import fnmatch
import sqlite3
import json
import os

BUFFER_SIZE = 1024
TIMEOUT = 30
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

        if file_data is None or file_data[0] is None:
            message = f"File: {filename} is not found"
            send_response(conn, 400, message)
            return
        send_response(conn, 200) # ACK
        
        # client needs to create file and receive file binary
        for i in range(0, len(file_data), BUFFER_SIZE):
            conn.sendall(file_data[i:i+BUFFER_SIZE])
        conn.sendall(b"EOF")

        send_response(conn, 200, data=file_data[0])
        print(f"Sent file: {filename} to client")

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
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
        
        # Check if files exists
        answer = ""
        cursor.execute("SELECT fileName FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))
        if cursor.fetchone():
            message = f"File: {filename} already exists. Replace it? (y/n)"
            send_response(conn, 400, message, data="replace")
            answer = conn.recv(BUFFER_SIZE).decode().strip().lower()

            if answer != "y":
                message = "OK upload terminated"
                send_response(conn, 400, message)
                return
        
        send_response(conn, 200) #ACK
    
        print("Receiving file...")

        fileData = b""
        while True:
            data = conn.recv(BUFFER_SIZE)
            if b"EOF" in data:
                fileData += data.replace(b"EOF", b"")
                break
            fileData += data

        print(f"File: '{filename}' received")

        type = get_file_type(filename)
        gb = len(fileData) / 1000000000
        max_size = get_max_size(type)
        if gb > max_size:
            message = f"File type: {type} cannot be greater than {max_size} GB"
            send_response(conn, 400, message)
            return

        size = len(fileData)
        cursor.execute("INSERT OR REPLACE INTO Files (fileName, fileParent, fileType, fileBytes, fileData) VALUES (?, ?, ?, ?, ?)", (filename, cwd, type, size, fileData))
        db.commit()

        message = f"File: {filename} sucessfully uploaded"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        return
    
    finally:
        db.close()


def cd(conn, cwd, new_dir, type):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    if type == "r":
        # make sure the dir exists, then return it
        cursor.execute("SELECT name FROM Directories WHERE parent = ?", (cwd,))
        if not cursor.fetchone():
            conn.send(f"Directory: {new_dir} does not exist")
            return

        if new_dir in [dir[0] for dir in cursor.fetchall()]:
            message = f"cd to {new_dir} successful"
            send_response(conn, 200, message, data=new_dir) # data is the actual new dir

    elif type == "b":
        cursor.execute("SELECT parent FROM Directories WHERE name = ?", (cwd,))
        if cursor.fetchone():
            new_dir = cursor.fetchone()[0]
            message = f"cd to {new_dir} successful"
            send_response(conn, 200, message, new_dir)

    # other types are clients fault, so should break
    db.close()
    

def ls(conn, cwd):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''SELECT Directories.name, Files.fileName FROM Directories
                        JOIN Files ON Directories.parent = Files.fileParent
                        WHERE Directories.parent = ? AND Files.fileParent = ?''', (cwd, cwd))
    
        if not cursor.fetchall():
            message = f"No files or directories in {cwd}"
            send_response(conn, 400, message)
            return

        message = f"Files / directories in {cwd}: "
        data = [name[0] for name in cursor.fetchall()]
        send_response(conn, 200, message, data)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        return


def delete(conn, filename, cwd):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT fileName FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))

        if not cursor.fetchone():
            message = f"File: {filename} does not exist in this directory"
            send_response(conn, 400, message)

        cursor.execute("DELETE FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))
        message = f"File: {filename} deleted"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        return

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

    cursor.execute('''SELECT fileName, fileType, fileBytes FROM Files WHERE fileParent = "home";''')
    print(cursor.fetchall())

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
    

# Returns max size of each type in gb's
def get_max_size(type):
    match type:
        case "audio":
            return 0.5
        case "text":
            return 0.025
        case "video":
            return 2
        case "image":
            return .01
        case _:
            return 1
        

def send_response(conn, status, message = None, data = None):
    response = {
        "status": status,
        "message": message,
        "data": data
    }

    print(message)
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
                cd(conn, args[1], args[2], args[3]) #cd cwd newdir (a,r,b)
            case "ls":
                ls(conn, args[1]) # ls cwd
            case "upload":
                upload(conn, args[1], args[2]) # upload filename cwd 
            case "download":
                download(conn, args[1], args[2]) # download filename cwd
            case "delete":
                delete(conn, args[1], args[2]) # delete filname cwd
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
        conn, address = server_socket.accept() # accept new connection
        conn.settimeout(TIMEOUT)  
        print("Connection from: " + str(address))
        start_new_thread(threaded_server, (conn,))

    conn.close()  
    
if __name__ == '__main__':
    run_server()

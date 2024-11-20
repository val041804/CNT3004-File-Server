import socket
from _thread import *
import threading
import sqlite3
import json
import os
from utils import *
import pickle

BUFFER_SIZE = 1024
TIMEOUT = None
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
        
        file_data = file_data[0]
        # client needs to create file and receive file binary
        for i in range(0, len(file_data), BUFFER_SIZE):
            conn.send(file_data[i:i+BUFFER_SIZE])
        conn.send(b"EOF")

        print(f"Sent file: {filename} to client")

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        return


def upload(conn, filename, cwd): #BUG: Huge zip upload breaks this
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM Directories WHERE name = ?", (cwd,))
        result = cursor.fetchone()
        if not result:
            message = f"Directory: {cwd} does not exist"
            send_response(conn, 400, message)
            return
        
        # Check if files exists
        answer = ""
        cursor.execute("SELECT fileName FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))
        if cursor.fetchall():
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
        result = cursor.fetchone()
        if not result:
            conn.send(f"Directory: {new_dir} does not exist")
            return

        cursor.execute("SELECT name FROM Directories WHERE parent = ?", (cwd,)) #written again bc fetch removes from the list of selected items
        if new_dir in [dir[0] for dir in cursor.fetchall()]:
            message = f"cd to {new_dir} successful"
            send_response(conn, 200, message, data=new_dir) # data is the actual new dir

    elif type == "b":
        cursor.execute("SELECT parent FROM Directories WHERE name = ?", (cwd,))
        result = cursor.fetchone()
        if result:
            new_dir = result[0]
            message = f"cd to {new_dir} successful"
            send_response(conn, 200, message, new_dir)

    # other types are clients fault, so should break
    db.close()
    

def ls(conn, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        cursor.execute('''SELECT DISTINCT name
                          FROM Directories
                          WHERE Directories.parent = ?''', (cwd,))
        dirs = cursor.fetchall()

        cursor.execute('''SELECT DISTINCT fileName
                          FROM Files
                          WHERE Files.fileParent = ?''', (cwd,))
        files = cursor.fetchall()

        if not dirs and not files:
            message = f"No files or directories in {cwd}"
            send_response(conn, 400, message)
            return

        send_response(conn, 200)
        objects = [name[0] for name in dirs]
        objects += [name[0] for name in files] 

        # pickle serializes array for transmission
        data = pickle.dumps(objects) #TODO should send two seperate data dumps for files vs dirs for color coding
        conn.sendall(data)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        return


def rm(conn, filename, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        cursor.execute("SELECT fileName FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))

        if not cursor.fetchone():
            message = f"File: {filename} does not exist in this directory"
            send_response(conn, 400, message)
            db.close()
            return

        cursor.execute("DELETE FROM Files WHERE fileName = ? AND fileParent = ?", (filename, cwd))
        db.commit()
        db.close()
        message = f"File: {filename} deleted"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        db.close()
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        db.close()
        return


def mkdir(conn, name, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        cursor.execute("INSERT INTO Directories(name, parent) VALUES(?, ?)", (name, cwd))
        db.commit()
        db.close()
        message = f"Successfully created directory: {name}"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        db.close()
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        db.close()
        return


def rmdir(conn, name, cwd):
    try:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        cursor.execute("SELECT name FROM Directories WHERE name = ? AND parent = ?", (name, cwd))

        if not cursor.fetchone():
            message = f"Directory: {name} does not exist in this directory"
            send_response(conn, 400, message)
            db.close()
            return

        cursor.execute("DELETE FROM Directories WHERE name = ? AND parent = ?", (name, cwd))
        db.commit()
        db.close()
        message = f"Directory: {name} deleted"
        send_response(conn, 200, message)

    except sqlite3.Error as e:
        message = f"Database error: {e}"
        send_response(conn, 400, message)
        db.close()
        return

    except Exception as e:
        message = f"Unexpected error: {e}"
        send_response(conn, 400, message)
        db.close()
        return    


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
            case "rm":
                rm(conn, args[1], args[2]) # delete filename cwd
            case "mkdir":
                mkdir(conn, args[1], args[2]) # mkdir name cwd
            case "rmdir":
                rmdir(conn, args[1], args[2])
            case "quit":
                break
        #send_response(....?)

    conn.close()  # close the connection


def run_server():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    setup_db(DB_NAME)


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

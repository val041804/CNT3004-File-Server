import socket
from _thread import *
import threading
import fnmatch
import sqlite3

SIZE = 1024
print_lock = threading.Lock()

def send_file(conn, file_name, cwd):
    # db_conn = sqlite3.connect('dbname.db')
    # db_cursor = db_conn.cursor()

    # Retrieve file

    # db_cursor.execute("SELECT * FROM files WHERE name = ? AND dir_id = ?", (file_name, cwd))
    # file_data = db_cursor.fetchone()
    # db_cursor.close()

    # if file_data is not None:
        # conn.sendall(file_data)
    pass


def upload(conn, file, cwd):

    db = sqlite3.connect('filesystem.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM directories WHERE id = ?", (cwd,))
    if not cursor.fetchone():
        conn.send("Directory: {cwd} does not exist")
        return
    
    filename = conn.recv(SIZE).decode()
    conn.send("Recieving file...").encode()


    with open(filename, 'wb') as file:
        while True:
            data = conn.recv(SIZE)
            if not data:
                break
            file.write(data)

    conn.send("File: '{filename}' received")

    type = get_file_type(filename)
    cursor.execute("INSERT INTO files (name, parent, type, data) VALUES (?, ?)", (filename, cwd, type, file))
    db.commit()
    conn.send("Uploaded file: {filename}")


def threaded_server(conn):
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(SIZE).decode()
        if not data:
            # if data is not received break
            break
        
        cmd = data.split()[0]
        args = data.split()[1:]

        match cmd:
            case "upload":
                upload(conn, args[1], args[2]) # upload filename cwd
                
                
        conn.send(str(f'{str_data} ---> received').encode())

    conn.close()  # close the connection


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
     

def run_server():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance

    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(5)

    while True:
        conn, address = server_socket.accept()  # accept new connection
        print("Connection from: " + str(address))
        start_new_thread(threaded_server, (conn,))

    conn.close()  # close the connection
    
if __name__ == '__main__':
    run_server()

import socket
import fnmatch

# conn = sqlite3.connect('filesystem.db')
# cursor = conn.cursor()

def cd(client_socket, cwd, arg):
    # checking for absolute path and relative path
    det_path = arg[0:3]

    match det_path:
        # absolute path
        case det_path if fnmatch.fnmatch(det_path, "/*"):
            #check if abs path exists, then return the path
            print("absolute path")
        case det_path if fnmatch.fnmatch(det_path, "./*"):
            #check if cwd + rel path exists, return whole path
            print("relative path")
        case det_path if fnmatch.fnmatch(det_path, "../*"):
            # go backwards
            print("backwards")


def ls(client_socket, cwd):
    # server returns array of current objects in cwd
    objects = ["dir1", "dir2", "dir3", "dir4", "file1"]
    for i in range(0, len(objects), 4):
        print("\t".join(objects[i:i+4]))


def upload(file_name, directory_id):

    # cursor.execute("SELECT id FROM directories WHERE id = ?", (directory_id,))
    # if not cursor.fetchone():
    #     print("Directory does not exist.")
    #     return
    
    # cursor.execute("INSERT INTO files (name, dir_id) VALUES (?, ?)", (file_name, directory_id))
    # conn.commit()
    # print(f"File '{file_name}' uploaded to directory ID {directory_id}.")

    pass


def download(file_name, directory_id):

    # Retrieve file
    # cursor.execute("SELECT * FROM files WHERE name = ? AND dir_id = ?", (file_name, directory_id))
    # file = cursor.fetchone()

    # if file:
    #     print(f"File '{file_name}' downloaded from directory ID {directory_id}.")
    # else:
    #     print("File does not exist in the specified directory.")
    pass


def delete(file_name, directory_id):

    # cursor.execute("DELETE FROM files WHERE name = ? AND dir_id = ?", (file_name, directory_id))
    # conn.commit()

    # if cursor.rowcount > 0:
    #     print(f"File '{file_name}' deleted from directory ID {directory_id}.")
    # else:
    #     print("File does not exist in the specified directory.")
    pass

def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
	
    message = ""
    cwd = 1
    while True:
        message = input("[user]$ ")
        if message == 'exit':
            break

        args = message.split(" ", 2)
        match args[0]:
            case "cd":
                #cwd = cd(client_socket, cwd, args[1])
                cd(client_socket, cwd, args[1])
            case "ls":
                ls(client_socket, cwd)
            case _:
                print("Unknown Command")

        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print(data)

    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

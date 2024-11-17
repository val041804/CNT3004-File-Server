import socket
import fnmatch
import os
import json

BUFFER_SIZE = 1024

def cd(client_socket, cwd, arg):
    # checking for absolute path and relative path
    det_path = arg[0:3]

    # NOTE FROM ANDREW: to do something like cd dir1/dir2, just have it call cd recursively, first on dir1, then dir2, .. etc
    # for absolute option, that can also be converted into recursive relative cd just starting from root
    # send first packet like: cd {cwd} {newDir} {(r,b)}
    #r: relative, b: backwards

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
    # objects = ["dir1", "dir2", "dir3", "dir4", "file1"]
    # for i in range(0, len(objects), 4):
    #     print("\t".join(objects[i:i+4]))

    pass


def upload(client_socket, filename, cwd):
    # ONLY HANDLES IF FILE IS IN LOCAL DIR

    # Check if the file exists
    if not os.path.isfile(filename):
        print(f"File '{filename}' does not exist.")
        return
    
    message = f"upload {filename} {cwd}"
    client_socket.send(message.encode())

    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    if response["status"] == 400:
        print(response["message"])
        if response["data"] != "replace":
            return
        
        # Answer y/n for replacing the file:
        answer = input()
        client_socket.send(answer.encode())
        response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
        if response["status"] == 400:
            print(response["message"])
            return

    # getting here means there was no errors and/or user entered y for replace

    print("Uploading file...")
    # Send the file data in chunks
    with open(filename, 'rb') as file:
        while chunk := file.read(BUFFER_SIZE):
            client_socket.send(chunk)
    client_socket.send(b'EOF') # signal end of file 

    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    if response["status"] == 400:
        print(response["message"])
        return
    
    print(response["message"])


def download(client_socket, file_name, cwd):

    # Request server to send_file

    pass


def delete(client_socket, file_name, cwd):

    # cursor.execute("DELETE FROM files WHERE name = ? AND dir_id = ?", (file_name, cwd))
    # conn.commit()

    # if cursor.rowcount > 0:
    #     print(f"File '{file_name}' deleted from directory ID {cwd}.")
    # else:
    #     print("File does not exist in the specified directory.")
    pass


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
	
    message = ""
    cwd = "home"
    print(os.getcwd())
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
            case "upload":
                upload(client_socket, args[1], cwd)
            case _:
                print("Unknown Command")


    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

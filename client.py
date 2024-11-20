import socket
import fnmatch
import os
import json
import pickle

BUFFER_SIZE = 1024
TIMEOUT = None

# https://stackoverflow.com/a/48706260
def get_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'Downloads')


def download(client_socket, file_name, cwd):

    # Request server to send_file
    message = f"download {file_name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            print(response["message"])
            return
        case 200:
            file_data = b""
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if b"EOF" in data:
                    file_data += data.replace(b"EOF", b"")
                    break
            file_data += data
    
    if file_data is None:
        print("Error downloading, try again.")
        return
    
    with open(f"{get_download_path()}/{file_name}", "wb") as file:
        file.write(file_data)


def upload(client_socket, path, cwd):
    # Get name of file from path
    filename = path.split("/")[-1]
    # Check if the file exists
    if not os.path.isfile(path):
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
    with open(path, 'rb') as file:
        while chunk := file.read(BUFFER_SIZE):
            client_socket.send(chunk)
    client_socket.send(b'EOF') # signal end of file 

    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    if response["status"] == 400:
        print(response["message"])
        return
    
    print(response["message"])

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
    # Request list of objects in cwd
    message = f"ls {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            print(response["message"])
            return
        case 200:
            print(response["message"])
            data = client_socket.recv(BUFFER_SIZE)
            objects = pickle.loads(data)
            for i in range(0, len(objects), 4):
                print("\t".join(objects[i:i+4]))


def delete(client_socket, file_name, cwd):
    # Request server to delete a file
    message = f"delete {file_name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            print(response["message"])
            return
        case 200:
            print(response["message"])
            return


def mkdir(client_socket, name, cwd):
    # Request server to make a directory
    message = f"mkdir {name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            print(response["message"])
            return
        case 200:
            print(response["message"])
            return


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_socket.settimeout(TIMEOUT)
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
            case "download":
                download(client_socket, args[1], cwd)
            case "delete":
                delete(client_socket, args[1], cwd)
            case "mkdir":
                mkdir(client_socket, args[1], cwd)
            case _:
                print("Unknown Command")


    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

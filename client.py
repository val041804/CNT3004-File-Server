import socket
import fnmatch
import os
import json
import pickle
import textwrap

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


def display_response(message, type):
    icons = {
        "success": "✅ SUCCESS",
        "error": "❌ ERROR",
        "warning": "⚠️  WARNING",
        "info": "🔍 INFO"
    }

    if type and message:
        print()
        bar_length = 50  
        wrapped_message = textwrap.fill(message, width=bar_length-4)  # Subtract 4 to account for the padding
        
        print("═" * bar_length)
        print(f" {icons[type]}")
        print("═" * bar_length)
        
        for line in wrapped_message.split("\n"):
            print(f" {line}")
        
        print("═" * bar_length)
        print()

def download(client_socket, file_name, cwd):

    # Request server to send_file
    message = f"download {file_name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], response["type"])
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
        message = "Error downloading, try again."
        display_response(message, "error")
        return
    
    with open(f"{get_download_path()}/{file_name}", "wb") as file:
        file.write(file_data)

    display_response("File downloaded.", "success")


def upload(client_socket, path, cwd):
    # Get name of file from path
    filename = path.split("/")[-1]
    # Check if the file exists
    if not os.path.isfile(path):
        display_response(f"File '{filename}' does not exist.", "error")
        return
    
    message = f"upload {filename} {cwd}"
    client_socket.send(message.encode())

    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    if response["status"] == 400:
        display_response(response["message"], response["type"])
        if response["data"] != "replace":
            return
        
        # Answer y/n for replacing the file:
        answer = input("Do you want to replace the file? (y/n): ")
        client_socket.send(answer.encode())
        response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
        if response["status"] == 400:
            display_response(response["message"], response["type"])
            return

    # getting here means there was no errors and/or user entered y for replace

    display_response("Uploading file...", "info")
    # Send the file data in chunks
    with open(path, 'rb') as file:
        while chunk := file.read(BUFFER_SIZE):
            client_socket.send(chunk)
    client_socket.send(b'EOF') # signal end of file 

    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    if response["status"] == 400:
        display_response(response["message"], "error")
        return
    
    display_response(response["message"], "success")


def cd(client_socket, cwd, new_dir):
    # Move backwards or forwards
    if new_dir == "../" or new_dir == "..":
        message = f"cd {cwd[0]} {new_dir} b"
    else:
        message = f"cd {cwd[0]} {new_dir} r"
    
    # Request server
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], response["type"])
            return
        case 200:
            print(response["data"])
            cwd[0] = response["data"]
    


def ls(client_socket, cwd):
    # Request list of objects in cwd
    message = f"ls {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], response["type"])
            return
        case 200:
            data = client_socket.recv(BUFFER_SIZE)
            objects = pickle.loads(data)
            for i in range(0, len(objects)):
                if objects[i] == cwd:
                    continue
                if i % 6 == 0 and i != 0:
                    print("\r")
                if '.' not in objects[i]:
                    print(f"\033[92m{objects[i]}\033[0m", end="\t")
                else:
                    print(f"{objects[i]}", end="\t")
            print("\r")




def rm(client_socket, file_name, cwd):
    # Request server to delete a file
    message = f"rm {file_name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], "error")
            return
        case 200:
            display_response(response["message"], "success")
            return


def mkdir(client_socket, name, cwd):
    # Request server to make a directory
    message = f"mkdir {name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], "error")
            return
        case 200:
            display_response(response["message"], "success")
            return


def rmdir(client_socket, name, cwd):
    # Request server to delete folder
    message = f"rmdir {name} {cwd}"
    client_socket.send(message.encode())

    # Wait for response
    response = json.loads(client_socket.recv(BUFFER_SIZE).decode())
    match(response["status"]):
        case 400:
            display_response(response["message"], "error")
            return
        case 200:
            display_response(response["message"], "success")
            return


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_socket.settimeout(TIMEOUT)
    message = ""
    cwd = ["home"]
    print(os.getcwd())
    while True:
        c_cwd = cwd[0]
        message = input(f"[user \033[92m{c_cwd}\033[0m]$ ")
        if message == 'exit':
            break

        args = message.split(" ", 2)
        match args[0]:
            case "cd":
                cd(client_socket, cwd, args[1])
            case "ls":
                ls(client_socket, c_cwd)
            case "upload":
                upload(client_socket, args[1], c_cwd)
            case "download":
                download(client_socket, args[1], c_cwd)
            case "rm":
                rm(client_socket, args[1], c_cwd)
            case "mkdir":
                mkdir(client_socket, args[1], c_cwd)
            case "rmdir":
                rmdir(client_socket, args[1], c_cwd)
            case _:
                display_response("Unknown Command", "error")


    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()


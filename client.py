import socket
import fnmatch

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


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
	
    message = ""
    cwd = "/"
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

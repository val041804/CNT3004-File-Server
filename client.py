import socket


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
	
    message = ""
    
    while True:
        message = input("[user]$ ")
        if message == 'exit':
            break
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print(data)

    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

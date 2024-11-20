
# Multithreaded File Transfer System - Documentation

## **Overview**

This system facilitates file management between a client and a server using a socket-based connection. It supports operations such as uploading, downloading, navigating directories, and managing files.

---

## **Commands**

### **1. `cd` (Change Directory)**
Changes the current working directory (CWD) of the client.
- **Usage**: `cd <path>`
  - Relative path (`subdir`)
  - Parent directory (`../`)
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `cwd`: Current working directory.
  - `arg`: Path argument.
- **Output**: Updates the current working directory.

---

### **2. `ls` (List Directory Contents)**
Lists the contents of the current directory.
- **Usage**: `ls`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `cwd`: Current working directory.
- **Output**: Displays directory contents, highlighting folders in green.

---

### **3. `upload`**
Uploads a file from the client to the server.
- **Usage**: `upload <file_path>`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `path`: Path to the file on the client.
  - `cwd`: Current working directory on the server.
- **Features**:
  - Checks if the file exists locally.
  - Prompts for overwrite if the file exists on the server.
  - Sends file data in chunks with a termination signal (`EOF`).

---

### **4. `download`**
Downloads a file from the server to the client.
- **Usage**: `download <file_name>`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `file_name`: Name of the file to download.
  - `cwd`: Current working directory on the server.
- **Features**:
  - Saves the file to the client’s default download directory.

---

### **5. `rm` (Remove File)**
Deletes a file on the server.
- **Usage**: `rm <file_name>`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `file_name`: Name of the file to delete.
  - `cwd`: Current working directory.
- **Output**: Confirms file deletion or reports an error.

---

### **6. `mkdir` (Make Directory)**
Creates a new directory on the server.
- **Usage**: `mkdir <directory_name>`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `name`: Name of the directory to create.
  - `cwd`: Current working directory.
- **Output**: Confirms directory creation or reports an error.

---

### **7. `rmdir` (Remove Directory)**
Deletes a directory on the server.
- **Usage**: `rmdir <directory_name>`
- **Parameters**:
  - `client_socket`: The client’s socket connection.
  - `name`: Name of the directory to delete.
  - `cwd`: Current working directory.
- **Output**: Confirms directory deletion or reports an error.

---

### **8. `exit`**
Terminates the client program.
- **Usage**: `exit`
- **Functionality**:
  - Closes the socket connection and exits the loop.

---


## **Constants**

- **`BUFFER_SIZE`**: Controls the size of data chunks exchanged between client and server (default: 1024 bytes).
- **`TIMEOUT`**: Specifies the socket timeout (default: `None`).

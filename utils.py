import sqlite3
import json

def setup_db(DB_NAME):
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

    if message:
        print(message)
    conn.send(json.dumps(response).encode())

CREATE TABLE IF NOT EXISTS Directories (
    name TEXT NOT NULL,
    parent TEXT,
    PRIMARY KEY (name, parent)
    FOREIGN KEY (parent) REFERENCES Directories(name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS File (
    fileID INTEGER PRIMARY KEY AUTOINCREMENT,
    fileName TEXT NOT NULL,
    fileParent TEXT NOT NULL,
    fileType TEXT NOT NULL,
    fileBytes FLOAT NOT NULL,
    fileData BLOB NOT NULL,
    FOREIGN KEY (fileParent) REFERENCES Directories(name) ON DELETE CASCADE
    
);

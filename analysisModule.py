# python module that collects statistics from our server module
import psutil
import time
import socket

# tracking download speeds
def download_speed(conn, filename, cwd):
    # starting timer
    start_timer = time.time() 
    try:
        size = 0
        for i in range(0, len(file_data), BUFFER_SIZE):
            chunk = file_data[i:i + BUFFER_SIZE]
            conn.send(chunk)
            size += len(chunk)

        conn.send(b"EOF")
        print(f'Sent file: {filename} to client.')

        # calculating file transfer rate and download speed
        end_timer = time.time()
        duration = end_timer - start_timer
        speed = (size / duration) * 8 / 1e6 # calculated in Mbps
        # metrics that are printed are: file size, file transfer rate, and download speed
        print(f'Download complete: {size} bytes in {duration: .2f} secs. Speed: {speed: .2f} Mbps')
    
    except Exception as e:
        print(f'Error during download: {e}')
# tracking upload speeds
def upload_speed(conn, filename, cwd):
    # starting timer
    start_timer = time.time()
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if b"EOF" in data:
                file_data += data.replace(b"EOF", b"")
                break
            file_data += data

        size = len(file_data)
        # ending timer
        end_timer = time.time()
        # calculations for file transfer rate and upload speed
        duration = end_timer - start_timer
        speed = (size / duration) * 8 / 1e6 # calculated in Mbps
        # metrics that are printed are: file size, file transfer rate, and upload speed
        print(f'Download complete: {size} bytes in {duration: .2f} secs. Speed: {speed: .2f} Mbps')

    except Exception as e:
        print(f'Error during download: {e}')

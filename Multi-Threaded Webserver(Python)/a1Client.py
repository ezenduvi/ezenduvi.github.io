import socket
import threading
import time

# Define the server's host and port
HOST = 'hawk.cs.umanitoba.ca'
PORT = 8153
#Number of requests to receive
REQUESTS = 90

#variables to count number of threads and lock variable to use while incrementing 
threadCount = 0
lock = threading.Lock()

# function to make a GET/HEAD request
def worker():
    global threadCount
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        #send the GET request
        client_socket.sendall(b'GET /images/png-1mb.png HTTP/1.1')
           
        #collect response in chunks until it has completely been received     
        response = b''
        while True:
            completeResponse = client_socket.recv(1048576)
            if not completeResponse:
                break
            response += completeResponse
        
        #use lock to increment threadCount   
        with lock:
            threadCount += 1
              
        client_socket.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    threads = []
    
    #track start time
    startTime = time.time()
    
    for _ in range(REQUESTS):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    #track end time, do math and print the realtime and number of threads ran
    endTime = time.time()
    realTime = endTime - startTime
    print(f"{realTime} {threadCount}")

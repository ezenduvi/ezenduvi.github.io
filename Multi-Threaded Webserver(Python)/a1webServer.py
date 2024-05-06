import socket
import threading
import sys
import os
import re
import pytz
import datetime

#check if -m flag for multithreading is present and set boolean value, if number of arguments is neither 3 0r 4 quit program
if len(sys.argv) == 3:
    multithread = False
    print("Multithread is", multithread)
elif len(sys.argv) == 4 and sys.argv[-1] == "-m":
    multithread = True
    print("Multithread is", multithread)
else:
    print("Invalid number of arguments")
    sys.exit()

# Symbolic name meaning all available interfaces
HOST = ''   
# Arbitrary non-privileged port (8150-8154)    
PORT = int(sys.argv[1]) 
PATH = sys.argv[2]

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                
name = socket.gethostname()     
ip = socket.gethostbyname(name)

#print host name, ip and port number
print("Host name:", name, "Host ip:", ip, "Port:", PORT)    

def workerThread(connection:socket):
    try:
        #convert data in bytes to string
        data = connection.recv(1024).decode("utf-8")        
        
        #check if it is a valid request (GET or HEAD)
        valid = re.match(r'^(GET|HEAD) /(.+?) HTTP', data)
        
        #if it is a get or head request then handle each cases else send response code
        if valid:
            #save request method and file requested in variables
            requestMethod = valid.group(1)
            requestFile = valid.group(2)
            
            #combine path webserver should serve and the file to get full path
            fullPath =  os.path.join(PATH, requestFile)
            
            #check if file exists
            if os.path.isfile(fullPath):
                #gather required information for http response header
                fileExt = os.path.splitext(fullPath)[1]
                
                #set contentType by checking file extension
                if fileExt == ".html":
                    contentType = "text/html"
                elif fileExt == ".json":
                    contentType = "application/json"
                elif fileExt == ".txt":
                    contentType = "text/plain"
                elif fileExt == ".jpeg":
                    contentType = "image/jpeg"
                elif fileExt == ".jpg":
                    contentType = "image/jpeg"
                elif fileExt == ".png":
                    contentType = "image/png"
                elif fileExt == ".js":
                    contentType = "text/javascript"
                elif fileExt == ".ico":
                    contentType = "image/x-icon"
                else:
                    badRequest = "HTTP/1.1 400 Bad Request\r\n\r\nFile Type Not Supported"
                    connection.sendall(badRequest.encode("utf-8"))
                    connection.close() 
                              
                #set lastModified with code in assignment description                   
                lastUpdatedPattern = "%a, %d %b %Y %H:%M:%S %Z"
                modifiedTimestamp = os.path.getmtime(fullPath)
                # hardcoding Winnipeg for simplicity
                modifiedTime = datetime.datetime.fromtimestamp(modifiedTimestamp, tz=pytz.timezone("America/Winnipeg"))
                lastModified = modifiedTime.strftime(lastUpdatedPattern)
                contentLength = os.path.getsize(fullPath)
                
                responseHeader = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {contentType}\r\n"
                    f"Content-Length: {contentLength}\r\n"
                    f"Last-Modified: {lastModified}\r\n"
                    f"Server: Stark Tower\r\n\r\n"
                )
                
                #take appropriate action if GET or HEAD
                if requestMethod == "GET":
                    #send response header and body
                    with open(fullPath, "rb") as bodyContent:
                        completeMsg = responseHeader.encode("utf-8") + bodyContent.read()
                        connection.sendall(completeMsg)
                        connection.close()
                        
                elif requestMethod == "HEAD":
                    #("it is a HEAD request")
                    #send response header only
                    responseHeader = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: {contentType}\r\n"
                        f"Last-Modified: {lastModified}\r\n"
                        f"Server: Stark Tower\r\n\r\n"
                    )
                    connection.sendall(responseHeader.encode("utf-8"))
                    connection.close
                    
            else:
            #send file not found response code
                notFound = "HTTP/1.1 404 Not Found\r\n\r\nFile not found."
                connection.sendall(notFound.encode("utf-8"))
                connection.close()     
                           
        else:
            badRequest = "HTTP/1.1 400 Bad Request\r\n\r\nThe request is neither a GET nor a HEAD request"
            connection.sendall(badRequest.encode("utf-8"))
            connection.close()
             
    except Exception as e:
        responseCode = "HTTP/1.1 500 Internal Server Error \r\n\r\n Internal Server Error."
        connection.sendall(responseCode.encode("utf-8"))
        connection.close()  

       
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
serverSocket.listen()

while True:
    try:
        (clientConnection, address) = serverSocket.accept()
        print(address, "has connected to the server")
        
        #use boolean we set initially to run in single/multi threaded mode
        if multithread:
            theThread = threading.Thread(target=workerThread, args=(clientConnection,))
            theThread.start()
            print("Running {} threads".format(threading.active_count()))
        else:
            workerThread(clientConnection)
            
    except KeyboardInterrupt as ki:
        print("Keyboard Interrupt")
        serverSocket.close()
        sys.exit()
    except Exception as e:
        print(e)
        print("whoops")

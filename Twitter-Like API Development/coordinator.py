import argparse
import json
import socket
import sys
import select

# ... (Other parts of your coordinator.py)

# List of worker addresses (host:port)
workers = []

# Round-robin index for load balancing
rr_index = 0

# Load balancing using round-robin
def get_worker(worker_clients):
    global rr_index
    worker = worker_clients[rr_index]
    rr_index = (rr_index + 1) % len(worker_clients)
    return worker 

# Function to initialize workers
def init_workers(worker_addresses):
    global workers
    workers = worker_addresses

# Start the coordinator
def start_coordinator(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind(('', port))
    serverSocket.listen()

    print(f'Coordinator listening on port {port}...')

    worker_clients = []

    for worker_address in workers:
        worker_host, worker_port = worker_address.split(':')
        workerconnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        workerconnection.connect((worker_host, int(worker_port)))
        print("connected to ", worker_host + ":" + worker_port)
        worker_clients.append(workerconnection)

    connections = [serverSocket] + worker_clients

    while True:
        print("waiting to receive message from webserver")

        try:
            rlist, _, _ = select.select(connections, [], [])

            for ready_socket in rlist:
                if ready_socket == serverSocket:
                    # New connection from a webserver
                    webserverconnection, address = serverSocket.accept()
                    print(address, "has connected to the server")
                    data_request = webserverconnection.recv(4096).decode('utf-8')

                    json_data = json.loads(data_request)
                    if json_data.get("type") == "SET":
                        for workerconnection in worker_clients:
                            # Send data_request(tweet) to worker
                            workerconnection.send(data_request.encode('utf-8'))

                            # Receive response from worker
                            response = workerconnection.recv(4096)
                            # Don't close workerconnection because we always want to stay connected

                            # Send response from worker back to webserver.py
                            webserverconnection.send(response)
                            # Close connection to webserver, when a new request is sent, it will open a new connection
                            # webserverconnection.close()
                            # Don't close workerconnection because coordinator must always be connected to workers
                    elif json_data.get("type") == "GET-DB":
                        #for workerconnection in worker_clients:
                        # Send data_request(tweet) to worker
                        workerconnection = get_worker(worker_clients)
                        workerconnection.send(data_request.encode('utf-8'))

                        # Receive response from worker
                        response = workerconnection.recv(4096)
                        # Don't close workerconnection because we always want to stay connected

                        # Send response from worker back to webserver.py
                        webserverconnection.send(response)
                        # Close connection to webserver, when a new request is sent, it will open a new connection
                        # webserverconnection.close()
                        # Don't close workerconnection because coordinator must always be connected to workers

        except KeyboardInterrupt as ki:
            print("Keyboard Interrupt")
            serverSocket.close()
            sys.exit()
        except Exception as e:
            print(e)
            print("whoops")

# Inside the main block
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help='Port number')
    parser.add_argument('workers', nargs='+', help='Worker host:port list')
    args = parser.parse_args()
    init_workers(args.workers)
    start_coordinator(args.port)

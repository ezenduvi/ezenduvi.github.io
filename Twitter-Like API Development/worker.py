import socket
import json
import uuid

class Tweet:
    def __init__(self, key, tweet_value):
        self.id = key
        self.lockstatus = "False"
        self.tweetvalue = tweet_value

# List to store Tweet objects
tweets_list = []

# Function to add a new tweet
def add_tweet(key, tweet_value):
    tweet = Tweet(key, tweet_value)
    tweets_list.append(tweet)
    return tweet.id 

# Function to get all tweets
def get_all_tweets():
    return [{"id": tweet.id, "lockstatus": tweet.lockstatus, "tweetvalue": tweet.tweetvalue} for tweet in tweets_list]

# Function to print all tweets
def print_all_tweets():
    for tweet in tweets_list:
        print(f"ID: {tweet.id}, Lock Status: {tweet.lockstatus}, Tweet Value: {tweet.tweetvalue}")

# Start the worker
def start_worker(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind(('', port))
    serverSocket.listen(1)

    print(f'Worker listening on port {port}...')
    coordconnection, address = serverSocket.accept()

    while True:
        
        print(address, "has connected to the server")
        data_request = coordconnection.recv(4096).decode('utf-8')

        response = ""
        json_data = json.loads(data_request)
        if json_data.get("type") == "SET":
            # Create and add a new tweet
            tweet_id = add_tweet(json_data.get("key"), json_data.get("value"))
            response = f"Success: Tweet added with ID {tweet_id}\n"
            print_all_tweets()
            
        elif json_data.get("type") == "CHECK":
            print("prepared to commit")
            
        elif json_data.get("type") == "GET-DB":
            # get all tweets
            print("getting all tweets in worker")
            all_tweets = get_all_tweets()
            response = json.dumps(all_tweets)
            print_all_tweets()
        #else:
            #response = "Invalid request\n"
            
            
        coordconnection.send(response.encode('utf-8'))
        #dont close coordconnection socket, we always want our coordinator to be connected to workers

# Inside the main block
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 worker.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    start_worker(port)

import socket
import sys
import threading
import json
import uuid

# Constants
HOST = ''
PORT = int(sys.argv[1])

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                
name = socket.gethostname()     
ip = socket.gethostbyname(name)

whoMadeTweet = []

#print host name, ip and port number
print("Host name:", name, "Host ip:", ip, "Port:", PORT)

# The address of the coordinator
COORDINATOR_ADDRESS = ('', 8153)  # Update to match the coordinator's address

# HTML skeleton with JavaScript 
index_html = """
<!DOCTYPE html>
<html>
  <head>
    <script>
      // JavaScript code posting to "Ecks"
      var username = "";
          
      //Handle login button click
      function login() {
        var display = document.getElementById("error");
        display.innerHTML = "";
        
        username = document.getElementById("username").value;
            
            
        //format body to send
        var requestData = "username=" + username;
            
        //set cookie to be body
        document.cookie = "username=" + username;
            
        //create xhr request and send to webserver
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/login", true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.send(requestData);
          
        //This event handler allows to handle responses in an asynchronous manner.
        xhr.onreadystatechange = function () {
          if (xhr.readyState === 4 && xhr.status === 200) {
              showPostForm();
              hideLoginForm()
              showTweetForm();
              getTweets();
          }
        };
      }
          
      //Handle checkLoginStatus
      function checkLoginStatus() {
        var cookies = document.cookie.split('; ');
        for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i];
          var parts = cookie.split('=');
          if (parts[0] === 'username') {
            //The "username" cookie exists, so the user is logged in
            showPostForm();
            hideLoginForm();
            showTweetForm();
            showErrorForm();
            //getTweets();             
            return true;
          }
        }
        // The "username" cookie doesn't exist, so the user is not logged in
        var display = document.getElementById("error");
        display.innerHTML = "Not logged in, Please log in first";
        showLoginForm();
        hidePostForm();
        hideTweetForm();
        //hideErrorForm();
        return false;
      }

      //Handle post button click
      function post() {
        // Implement your post logic here using XMLHttpRequest
        if(checkLoginStatus()){
          var tweet = document.getElementById("tweet").value;
              
          //create xhr request and send to webserver
          var xhr = new XMLHttpRequest();
          xhr.open("POST", "/api/tweet", true);
          xhr.setRequestHeader("Content-Type", "text/plain");
          xhr.send(tweet);
          xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
              getTweets()
            }
          };    
        };
        
      }
          
      function getTweets() {
        var xhr = new XMLHttpRequest();
        
        xhr.open("GET", "/api/tweet", true);
        xhr.setRequestHeader("Content-Type", "text/plain");
        //xhr.setRequestHeader("Accept", "application/json");
        xhr.send();
      }

      //Handle update button click
      function update(tweetId) {
              
      }

      // Hide post form
      function hidePostForm() {
        document.getElementById("postForm").style.display = "none";
      }
          
      // Hide tweet form
      function hideTweetForm() {
        document.getElementById("tweets").style.display = "none";
      }
      
      // Hide login form
      function hideLoginForm() {
          document.getElementById("loginForm").style.display = "none";
      }
      
      function hideErrorForm() {
          document.getElementById("error").style.display = "none";
      }

      // Show post form 
      function showPostForm() {
        document.getElementById("postForm").style.display = "block";
      }
          
      // show login form
      function showLoginForm() {
        document.getElementById("loginForm").style.display = "block";  
      }
          
      //show tweet form
      function showTweetForm() {
        document.getElementById("tweets").style.display = "block";
      } 
      
      function showErrorForm() {
        document.getElementById("error").style.display = "block";
      } 
       //onload="checkLoginStatus()" 
    </script>
  </head>
    <body>
      <h1>Ecks</h1>
      <div id="loginForm">
        <input type="text" id="username" placeholder="Enter your username">
        <button onclick="login()">Log in</button>
      </div>
      <div id="postForm" style="display: none;">
        <input type="text" id="tweet" placeholder="What's on your mind?">
        <button onclick="post()">Send it</button>
      </div>
      <div id="tweets" style="display: none;"></div>
      <div id="error" style="display: block;"></div>
      <div id="newest" style="display: block;"></div>
      <div id="test" style="display: block;"></div>
    </body>
</html>
"""


# Function to handle client requests
def workerThread(connection:socket):
  try:
    request = connection.recv(4096).decode('utf-8')
    
    if request.startswith("GET /api/tweet"):
      # Implement API handling for GET requests
        
      headers, body = request.split("\r\n\r\n", 1)

      # Split headers into lines
      header_lines = headers.split("\r\n")

      # Find and extract the Cookie header
      cookie_header = next((line for line in header_lines if line.startswith("Cookie: ")), None)

      # Extract the cookie value
      if cookie_header:
        cookie_value = cookie_header.split("Cookie: username=")[1]
      else:
        print("No Cookie found in the request.")
        
      tweet = {
        "type": "GET-DB"
      }
        
      json_string = json.dumps(tweet)

      # Send the tweet to the coordinator for 2PC processing
      coordinatorconnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      coordinatorconnection.connect(COORDINATOR_ADDRESS)
      coordinatorconnection.send(json_string.encode('utf-8'))
      response = coordinatorconnection.recv(4096).decode('utf-8')
      print("These are my tweets still in json format: "+ response+ "\n")
      
      response_cleaned = response[1:-1]
      
      tweets_div = '<div id="newest" style="display: block;">' + response_cleaned + '</div>'
      modified_html = index_html.replace('<div id="newest" style="display: block;"></div>', tweets_div)
    
      fullresponse = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + modified_html
      connection.send(fullresponse.encode('utf-8'))
        
    elif request.startswith("POST /api/tweet"):
      # Implement API handling for POST requests
        
      headers, body = request.split("\r\n\r\n", 1)

      # Split headers into lines
      header_lines = headers.split("\r\n")

      # Find and extract the Cookie header
      cookie_header = next((line for line in header_lines if line.startswith("Cookie: ")), None)

      # Extract the cookie value
      if cookie_header:
        cookie_value = cookie_header.split("Cookie: username=")[1]
      else:
        print("No Cookie found in the request.")
        
      #id to attach to message
      id = str(uuid.uuid4())
      
      # Create a JSON object with id and cookie_value
      value = {
        "id": id,
        "cookie_value": cookie_value,
      }

      # Store the JSON object in the list
      whoMadeTweet.append(value)
    
      tweet = {
        "type": "SET",
        "key": id,
        "value": body,
      }
        
      json_string = json.dumps(tweet)

      # Send the tweet to the coordinator for 2PC processing
      coordinatorconnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      coordinatorconnection.connect(COORDINATOR_ADDRESS)
      coordinatorconnection.send(json_string.encode('utf-8'))
      response = coordinatorconnection.recv(4096).decode('utf-8')
      print("The response i got from worker is ", response)

      response = "HTTP/1.1 200 OK\r\n\r\n"
      connection.send(response.encode('utf-8'))
        
    elif request.startswith("PUT /api/tweet/"):
      # Implement API handling for updating a tweet
      # Extract tweet ID and update the tweet
      tweet_id = request.split('/')[3]
      content_length = 0
      for line in request.split('\n'):
          if line.startswith("Content-Length: "):
              content_length = int(line.split(' ')[1])
      tweet_data = connection.recv(content_length).decode('utf-8')
          
      # Send the tweet update request to the coordinator for 2PC processing
      coordinatorconnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      coordinatorconnection.connect(COORDINATOR_ADDRESS)
      coordinatorconnection.send(request.encode('utf-8'))
      coordinatorconnection.close()
          
      response = "HTTP/1.1 200 OK\r\n\r\n"
      connection.send(response.encode('utf-8'))
        
    elif request.startswith("POST /api/login"):
      # Implement login logic and set cookies
      response = "HTTP/1.1 200 OK\r\n\r\n"
      connection.send(response.encode('utf-8'))

    elif request.startswith("GET /"):
      # Serve the HTML skeleton
      checkLogin = """
      <script>
        checkLoginStatus(); // Calling the checkLoginStatus function
      </script>
      """
      full_html = index_html + checkLogin
      
      response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + full_html
      connection.send(response.encode('utf-8'))
        
    else:
    # Handle other paths or errors
        
      error = "400 bad request"
      error_div = '<div id="error" style="display: block;">' + error + '</div>'
      modified_html = index_html.replace('<div id="error" style="display: block;"></div>', error_div)
    
      response = "HTTP/1.1 404 OK\r\nContent-Type: text/html\r\n\r\n" + modified_html
      connection.send(response.encode('utf-8'))
        
    connection.close()
    
  except Exception as e:
    error = "500 internal server error"
    error_div = '<div id="error" style="display: block;">' + error + '</div>'
    modified_html = index_html.replace('<div id="error" style="display: block;"></div>', error_div)
    
    response = "HTTP/1.1 500\r\nContent-Type: text/html\r\n\r\n" + modified_html
    connection.send(response.encode('utf-8'))
    connection.close()
    
           
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
serverSocket.listen()

while True:
  try:
    (clientConnection, address) = serverSocket.accept()
    print(address, "has connected to the server")    
       
    theThread = threading.Thread(target=workerThread, args=(clientConnection,))
    theThread.start()        
  except KeyboardInterrupt as ki:
    print("Keyboard Interrupt")
    serverSocket.close()
    sys.exit()
  except Exception as e:
    print(e)
    print("whoops")

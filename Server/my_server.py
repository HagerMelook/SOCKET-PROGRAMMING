from socket import *
import os, re, sys, threading, time

SERVER_PORT = 80
SERVER_IP = gethostbyname(gethostname())
server_socket = socket(AF_INET,SOCK_STREAM)

current_connections = 0
connection_timeout = 10
lock = threading.Lock()

def handleConnection(connection_socket, client_addr):
    # This will determine from which client this request come from
    print(f"This packet come from {client_addr}")
    global current_connections

    # Increase the number of connections
    with lock:
        current_connections += 1

    # This heuristic will work correctly as when number of connection increase, the timeout will decrease and vice verse
    connection_socket.settimeout(connection_timeout//current_connections)
    while True:
        try:
            # Use buffer of size 2048 to recv the GET or POST request
            msg = connection_socket.recv(2048).decode("UTF-8")
            if not msg:
                break
            print(msg)

            # Use the first line only to determine the method and the file path
            get_line = msg.splitlines()[0]
            method, path, *_ = get_line.split()

            # In case of request from web browser or from absolute path, you need to remove the slash
            path = path.lstrip('/')

            if method == "GET":
                # In case that the file exist
                if os.path.exists(path):
                    if path.endswith('.html') or path.endswith('.txt'):
                        with open(path, 'r') as file:
                            response_body = file.read()+"\r\n"
                            if path.endswith('.html'):
                                content_type = "text/html"  
                            else: content_type="text/plain"

                            response_headers = (
                                "HTTP/1.1 200 OK\r\n"
                                f"Host: {gethostname()}\r\n"
                                F"Content-Type: {content_type}\r\n"
                                f"Content-Length: {len(response_body)}\r\n\r\n"
                            )

                        response = response_headers + response_body
                        response = response.encode("UTF-8")
                        print(response)

                        # Send the content in chunks of size 2048
                        chunk_size = 2048
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i:i + chunk_size]
                            connection_socket.send(chunk)

                    else:
                        # Use the binary mode reading to read the byte array of the image
                        with open(path, 'rb') as file:
                            response_body = file.read()
                            if path.endswith('.jpg') or path.endswith('.jpeg'):
                                content_type = "image/jpeg"
                            elif path.endswith('.png'):
                                content_type = "image/png"
                            else:
                                content_type = "application/octet-stream"  # fallback type
                            response_headers = (
                                "HTTP/1.1 200 OK\r\n"
                                f"Host: {gethostname()}\r\n"
                                f"Content-Type: {content_type}\r\n"
                                f"Content-Length: {len(response_body)}\r\n\r\n"
                            )
                        # We don't encode the response body as it is byte array
                        response = response_headers.encode("UTF-8")+response_body+"\r\n".encode("UTF-8")
                        # Send the content in chunks of size 2048
                        chunk_size = 2048
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i:i + chunk_size]
                            connection_socket.send(chunk)

                # In case that the file is not exist
                else:
                    response = f"HTTP/1.1 404 Not Found\r\nHost: {gethostname()}\r\n\r\n"
                    connection_socket.send(response.encode("UTF-8"))

            if method == "POST":
                # Get the file name from the path
                file_name = os.path.basename(path)
                # Send the OK msg and wait for upload the file content
                response = f"HTTP/1.1 200 OK\r\nHost: {gethostname()}\r\n\r\n"
                connection_socket.send(response.encode("UTF-8"))

                # find the length of the file
                for line in msg.splitlines():
                    if line.startswith("Content-Length:"):
                        _,length = line.split(":", 1)
                        break
                
                # Receive the file in chunks and store it in the file
                chunk_size = 2048
                body = b""
                for i in range(0, int(length), chunk_size):
                    body = body + connection_socket.recv(2048)

                if path.endswith('.html') or path.endswith('.txt'):
                    body = body.decode("UTF-8")
                    print(body)
                    with open(file_name, 'w') as file:
                        file.write(body)
                else:
                    print(body)
                    with open(file_name, 'wb') as file:
                        file.write(body)

            time.sleep(0.1) 

        # The server doesn't receive any request for time period (idle connection)
        except timeout:
            print("Connection is closed, time out")
            connection_socket.close()
            break
    
    # Decrease the number of connections
    with lock:
        current_connections -= 1

def handShake ():
    # Allow the server to handshake any number of connections
    server_socket.listen()
    while True:
        # Accept the connection and create new socket for this client
        connection_socket, client_addr = server_socket.accept()
        print(f"Start connection with client {client_addr}")
        # Create new thread for each connection
        # We mention the reason why we use threads rather than processes in the report
        client_thread = threading.Thread(target=handleConnection, args=(connection_socket, client_addr))
        client_thread.start()

if len(sys.argv) < 2:
    print("Error: Port number required")
else:
    SERVER_PORT = int(sys.argv[1])
    SERVER_ADDR = (SERVER_IP,SERVER_PORT)
    server_socket.bind(SERVER_ADDR)
    handShake()
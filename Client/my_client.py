import os, sys
import re
from socket import *

SERVER_PORT = 8080
SERVER_IP = ""
client_socket = socket(AF_INET,SOCK_STREAM)


def get_msg(path):
    # Get the file name
    file_name = os.path.basename(path)

    # Send the get request
    get_msg = f"GET {path} HTTP/1.1\r\nHost: {(SERVER_IP)}\r\n\r\n"
    client_socket.send(get_msg.encode("UTF-8"))

    # receive the first chunk
    response = client_socket.recv(2048)
    msg = response
    length = -1
    for line in msg.splitlines():
        if line.decode("UTF-8").startswith("Content-Length:"):
            _,length = line.decode("UTF-8").split(":", 1)
            break

    # receive the remaining chunks
    chunk_size = 2048
    if length != -1:
        for i in range(0, int(length)-2048, chunk_size):
            response = response + client_socket.recv(2048)
    
    # write the content in the file
    if path.endswith('.html') or path.endswith('.txt'):
        response = response.decode("UTF-8")
        print(response)
        _,body = re.split(r'\r\n\r\n',response)
        if body:
            with open(file_name, 'w') as file:
                file.writelines(body)
    else: 
        header,body = response.split(b'\r\n\r\n')
        header = header.decode("UTF-8")
        print(header)
        print()
        if body:
            body,_ = body.split(b'\r\n')
            print(body)
            print()
            with open(file_name, 'wb') as file:
                file.write(body)

def post_msg(path):
    # Check if the file exist or not
    if os.path.exists(path):
        if path.endswith('.html') or path.endswith('.txt'):
            with open(path, 'r') as file:
                data = file.read()+"\r\n"
                # Determine the type of the content
                content_type = "text/html" if path.endswith('.html') else "text/plain"

            post_msg = (
                f"POST /{path} HTTP/1.1\r\n"
                f"Host: {(SERVER_IP)}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(data)}\r\n\r\n"
            )
            
            # Send the header first and receive the OK msg
            client_socket.send(post_msg.encode("UTF-8"))
            response = client_socket.recv(2048).decode("UTF-8")
            print(response)

            # Send the body in chunks of size 2048
            chunk_size = 2048
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                client_socket.send(chunk.encode("UTF-8"))

        else:
            with open(path, 'rb') as file:
                data = file.read()  
            # Determine the type of the content
            if path.endswith('.jpg') or path.endswith('.jpeg'):
                content_type = "image/jpeg"
            elif path.endswith('.png'):
                content_type = "image/png"
            else:
                content_type = "application/octet-stream" 

            post_msg = (
                f"POST /{path} HTTP/1.1\r\n"
                f"Host: {(SERVER_IP)}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(data)}\r\n\r\n"
            )
            # Send the header first and receive the OK msg
            client_socket.send(post_msg.encode("UTF-8")) 
            response = client_socket.recv(2048).decode("UTF-8")
            print(response)
            # Send the body in chunks of size 2048
            chunk_size = 2048
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                client_socket.send(chunk)
    # In case of the file not exist
    else:
        print("Cannot Find File")


def start():
    input_file_path = input("Enter the input_file path: ")

    with open(input_file_path, 'r') as file:
        lines = file.readlines()
        SERVER_ADDR = (SERVER_IP,SERVER_PORT)

        # Start the connection with the server
        client_socket.connect(SERVER_ADDR)
        print(lines)
        for line in lines:
            attributes = line.split()
            method, path,*_ = attributes
            if method == "client_get":
                get_msg(path)
            elif method == "client_post":
                post_msg(path)
        
        # The clint shut down at the end of the input file
        print("End of the file, the connection is closed")
        client_socket.close()

if len(sys.argv) < 3:
    print("Error: Enter python ./my_client.py [server_ip] [port_number]")

else:
    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    start()





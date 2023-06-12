from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
from time import sleep
import socket
import json
import threading
from datetime import datetime


HOST = "0.0.0.0"
HTTP_PORT = 3000
UDP_IP = '127.0.0.1'
UDP_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
   
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        redirect_data_to_socket_server(data_dict)
        self.send_response(302)
        self.send_header('Location','/')
        self.end_headers()
        
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
            
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())
              
def redirect_data_to_socket_server(data_dict):
    data = json.dumps(data_dict).encode('utf-8')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        server = (UDP_IP, UDP_PORT)
        sock.sendto(data, server)

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HOST, HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, UDP_PORT))
        result = {}
        while True:            
            data, _ = sock.recvfrom(8192)
            data_json = json.loads(data.decode("utf-8"))
            time_key = datetime.now().isoformat()
            result[time_key] = data_json
            with open('storage/data.json', "w", encoding="utf-8") as f:
                f.write(json.dumps(result) + '\n')
            print(result)

if __name__ == '__main__':
    threads = []
    http_server_thread = threading.Thread(target=run_http_server)
    http_server_thread.start()
    threads.append(http_server_thread)
    
    socket_server_thread = threading.Thread(target=run_socket_server)
    socket_server_thread.start()
    threads.append(socket_server_thread)
    
    for thread in threads:
        thread.join()
    
    
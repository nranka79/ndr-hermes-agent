from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import os

class FileHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Expecting JSON or simple base64
        try:
            # Assuming it's just raw base64 or similar
            with open('ndr_aadhar_received.pdf', 'wb') as f:
                f.write(base64.b64decode(post_data))
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File received successfully")
            print("--- FILE RECEIVED ---")
            os._exit(0) # Exit server after receiving
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())

def run():
    server_address = ('127.0.0.1', 8888)
    httpd = HTTPServer(server_address, FileHandler)
    print("Serving on 127.0.0.1:8888...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()

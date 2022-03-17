import argparse
import http.server
import json
import socketserver


class ConfigStorage:
    def __init__(self):
        self.credentialsStore = {"user@email.com": "password"}


class Auth(http.server.BaseHTTPRequestHandler):
    def __init__(self, configStore, *args):
        self.configStore = configStore
        http.server.BaseHTTPRequestHandler.__init__(self, *args)

    def do_POST(self, ):
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len)
        body = json.loads(body)
        if self.validate(body["username"], body["password"]):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("", "utf-8"))
        else:
            self.send_response(401)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("", "utf-8"))
        return


    def validate(self, username, password):
        try:
            return self.configStore.credentialsStore[username] == password
        except:
            return False
def main(serverPort: int, debugMode: bool) -> None:

    assert serverPort > 0 and serverPort < 65535, "Server port not in a valid range!"

    configStorage = ConfigStorage()  # type: ignore

    def handler_object(*args):
        return Auth(configStorage, *args)

    sensorConfigServer = socketserver.TCPServer(("", serverPort), handler_object)

    print(f"Server is listening on port {serverPort}.")
    sensorConfigServer.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Configuration distribution server for the key sensors."
    )
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--debug", required=False, action="store_true")

    parsed_args = parser.parse_args()

    main(parsed_args.port, parsed_args.debug)

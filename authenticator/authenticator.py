import argparse
import http.server
import json
import socketserver

import bcrypt
from dbservice import DBService

class Auth(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args):
        self.dbService = DBService()
        http.server.BaseHTTPRequestHandler.__init__(self, *args)

    def respond(self, status, msg):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(msg, "utf-8"))

    def do_POST(self):
        if self.path == "/login":
            self.login()
        if self.path == "/permission":
            self.checkPermission()
        if self.path == "/signup":
            self.signup()

    def signup(self):
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len)
        body = json.loads(body)
        username, password = (body["username"], body["password"])
        password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            self.dbService.signup(username, password.decode("utf-8"))
            self.respond(200, "")
        except Exception as e:
            self.respond(500, f"{e}")

    def login(self):
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len)
        body = json.loads(body)
        if self.validate(body["username"], body["password"]):
            self.respond(200, "")
        else:
            self.respond(401, "")
        return

    def checkPermission(self):
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len)
        body = json.loads(body)
        try:
            if self.dbService.checkPermission(body["username"], body["permission"]):
                self.respond(200, "")
            else:
                self.respond(403, "Insufficient permissions")
        except Exception:
            self.respond(401, "User not found")

    def validate(self, username, password):
        # try:
        hashedPass = self.dbService.getHashedPassword(username)

        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashedPass.encode("utf-8"),
        )


def main(serverPort: int, debugMode: bool) -> None:

    assert serverPort > 0 and serverPort < 65535, "Server port not in a valid range!"
    # type: ignore

    def handler_object(*args):
        return Auth(*args)

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

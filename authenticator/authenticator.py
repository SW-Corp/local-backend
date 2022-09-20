import argparse
import http.server
import json
import socketserver

import bcrypt
from dbservice import DBService

# "user@email.com": "$2b$12$yOaeOCNaJybzzO7s13W06ur7bY4E82L.JdKJOkxfqHdY1EXT3Brh."


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
        if self.path == "/usr":
            self.userExists()
        if self.path == "/signup":
            self.signup()

    def signup(self):
        content_len = int(self.headers.get("Content-Length"))
        print(content_len)
        body = self.rfile.read(content_len)
        body = json.loads(body)
        print(body["username"], body["password"])
        username, password = (body["username"], body["password"])
        password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            self.dbService.signup(username, password.decode("utf-8"))
            self.respond(200, "")
        except Exception as e:
            self.respond(500, f"{e}")

    def login(self):
        content_len = int(self.headers.get("Content-Length"))
        print(content_len)
        body = self.rfile.read(content_len)
        body = json.loads(body)
        print(body["username"], body["password"])
        if self.validate(body["username"], body["password"]):
            self.respond(200, "")
        else:
            self.respond(401, "")
        return

    def userExists(self):
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len)
        body = json.loads(body)
        if self.dbService.userExist(body["username"]):
            self.respond(200, "")
        else:
            self.respond(404, "No such user")

    def validate(self, username, password):
        # try:
        hashedPass = self.dbService.getHashedPassword(username)
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashedPass.encode("utf-8"),
            )
        except Exception:
            return False


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

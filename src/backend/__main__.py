import configargparse
import uvicorn

from .controllers import AuthConfig
from .http_server import HTTPServer
from .services.db_service import DBConfig
from .services.influx_service import InfluxConfig


def main():
    parser = configargparse.ArgParser()

    parser.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        help="The configuration file",
    )

    parser.add_argument(
        "--address",
        type=str,
        required=True,
        help="Address of backend",
    )

    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port of backend",
    )

    parser.add_argument(
        "--secret-key",
        type=str,
        required=True,
        help="Secret key of authenticator",
    )

    parser.add_argument(
        "--auth-addr",
        type=str,
        required=True,
        help="Address of authenticator",
    )

    parser.add_argument(
        "--auth-port",
        type=int,
        required=True,
        help="Port of authenticator",
    )

    parser.add_argument(
        "--authmode",
        type=str,
        required=True,
        help="Mode of authenticator",
    )

    parser.add_argument(
        "--auth-ttl",
        type=int,
        help="Time to live of authenticator",
        default=24 * 60 * 60,
    )

    parser.add_argument(
        "--db-user",
        type=str,
        required=True,
        help="Username of database",
    )

    parser.add_argument(
        "--db-password",
        type=str,
        required=True,
        help="Password of database",
    )

    parser.add_argument(
        "--db-host",
        type=str,
        required=True,
        help="Hostname of database",
    )

    parser.add_argument(
        "--db-port",
        type=int,
        required=True,
        help="Port of database",
    )

    parser.add_argument(
        "--db",
        type=str,
        required=True,
        help="Database",
    )

    parser.add_argument(
        "--influx-address",
        type=str,
        required=True,
        help="Address of influx",
    )

    parser.add_argument(
        "--influx-port",
        type=str,
        required=True,
        help="Port of influx",
    )

    parser.add_argument(
        "--influx-token",
        type=str,
        required=True,
        help="Token of influx",
    )

    parser.add_argument(
        "--influx-org",
        type=str,
        required=True,
        help="Organization name of influx",
    )

    args, _ = parser.parse_known_args()

    auth_config = AuthConfig(
        port=args.auth_port,
        secret_key=args.secret_key,
        addr=args.auth_addr,
        mode=args.authmode,
        auth_ttl=args.auth_ttl,
    )

    db_config = DBConfig(
        port=args.db_port,
        user=args.db_user,
        password=args.db_password,
        host=args.db_host,
        db=args.db,
    )

    influx_config = InfluxConfig(
        address=args.influx_address,
        port=args.influx_port,
        token=args.influx_token,
        org=args.influx_org,
    )

    http_server = HTTPServer(auth_config, db_config, influx_config)
    app = http_server.build_app()
    uvicorn.run(
        app,
        host=args.address,
        port=args.port,
        lifespan="on",
    )

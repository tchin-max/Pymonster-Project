"""Example pybeasts client implementing random movement and splitting"""

import argparse
import asyncio
from collections import namedtuple
import os
import random
import signal
import ssl
import sys
import websockets
from websockets import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

# accept self-signed certificate
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def print_and_flush(message: str):
    """
    Prints a given message to the console and flushes the
    output stream.

    Args:
        message (str): The message to be printed.

    Returns:
        None
    """
    print(message)
    sys.stdout.flush()


Command = namedtuple(
    "Command",
    [
        "BEAST_COMMAND_REQUEST",
        "BEAST_GONE_INFO",
        "NO_BEASTS_LEFT_INFO",
        "SHUTDOWN_INFO",
        "MOVE",
        "SPLIT",
    ],
)

cmd = Command(
    BEAST_COMMAND_REQUEST="BEAST_COMMAND_REQUEST",
    BEAST_GONE_INFO="BEAST_GONE_INFO",
    NO_BEASTS_LEFT_INFO="NO_BEASTS_LEFT_INFO",
    SHUTDOWN_INFO="SHUTDOWN_INFO",
    MOVE="MOVE",
    SPLIT="SPLIT",
)


async def handle_beast_command_request(
    websocket: WebSocketClientProtocol,
    beast_id: int,
    energy: float,
    environment: str,
) -> int | None:
    """
    Handle a beast in the game.  This sample function performs a random
    movement.

    Args:
        websocket: WebSocketClientProtocol: Connection to the server.
        beast_id (int): The ID of the beast.
        energy (float): The energy level of the beast.
        environment (str): The environment as 1d string.
    """
    if energy > 100 and not ">" in environment:
        d_x, d_y = random.choice(((0, 1), (0, -1), (-1, 0), (1, 0)))
        server_command = f"{beast_id} {cmd.SPLIT} {d_x} {d_y}"
    else:
        if random.randint(0, 12345) % 5 == 0:
            # completely random movement
            d_x = random.randint(-2, 2)
            d_y = random.randint(-2, 2)
        else:
            # move right
            d_x, d_y = 1, 0
        server_command = f"{beast_id} {cmd.MOVE} {d_x} {d_y}"
    print_and_flush(f'sending "{server_command}"')
    # don't change the next line or you will break the protocol
    await websocket.send(server_command)
    server_str = await websocket.recv()
    if "ERROR" in server_str:
        print_and_flush(server_str)
        success_str = "False"
        new_beast_id_str = "None"
    else:
        new_beast_id_str, success_str = server_str.split("#")
    # successful split
    if success_str == "True" and new_beast_id_str != "None":
        new_beast_id = int(new_beast_id_str)
        return new_beast_id
    return None


async def handle_beast_gone(
    beast_id: int,
    energy: float,
    environment: str,
) -> None:
    """
    Handle the situation of a beast starving to death or being eaten
    by another beast.

    Args:
        beast_id (int): The ID of the beast.
        energy (float): The energy level of the beast.
        environment (str): The environment as 1d string.
    """
    # replace this ...
    print_and_flush(f"beast {beast_id} with energy {energy} gone")
    print_and_flush(f"  environment: {environment}")


async def handle_no_beasts_left() -> None:
    """
    Handles the case when there are no beasts left.
    """
    # replace this ...
    print_and_flush("No beasts left")
    await handle_shutdown()


async def handle_shutdown():
    """
    Handles the shutdown event.

    This function is responsible for gracefully handling the shutdown event.
    It prints "bye" to the console.
    """
    # replace this ...
    print_and_flush("bye")
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGTERM)


################################################################################
# No need to change functionality below this line
# You should remove most of the debug print statements to save disk space.
################################################################################


async def client_loop(
    username: str, password_file_name: str, hostname: str, port: int
):
    """
    Asynchronously connects to a websocket server and performs a client loop.

    Args:
        username (str): The username for authentication.
        password_file_name (str): Name of file containing password
            for authentication.
        hostname (str): The hostname of the websocket server.
        port (int): The port number of the websocket server.

    Returns:
        None
    """
    try:
        with open(password_file_name, "r", encoding="utf-8") as password_file:
            password = password_file.read().rstrip("\n")
            password = password.strip()
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        raise e("Error reading Password file") from e

    async with websockets.connect(
        f"wss://{hostname}:{port}/login",
        ssl=ssl_context,
    ) as websocket:
        await websocket.send(f"{username}:{password}")
        server_str = await websocket.recv()
        # the server creates one beast with random position and the
        # start energy
        print_and_flush(f"Reply from server: {server_str!r}")
        while True:
            try:
                server_str = await websocket.recv()
                # remove this output eventually ...
                print_and_flush(f"{server_str = }")
                match server_str:
                    case cmd.BEAST_COMMAND_REQUEST:
                        id_energy_env = await websocket.recv()
                        print_and_flush(f"{id_energy_env = }")
                        (
                            beast_id_str,
                            energy_str,
                            environment_str,
                        ) = id_energy_env.split("#")
                        beast_id = int(beast_id_str)
                        energy = float(energy_str)
                        environment_str = str(environment_str)
                        await handle_beast_command_request(
                            websocket, beast_id, energy, environment_str
                        )
                    case cmd.BEAST_GONE_INFO:
                        id_energy_env = await websocket.recv()
                        print_and_flush(f"{id_energy_env = }")
                        (
                            beast_id_str,
                            energy_str,
                            environment_str,
                        ) = id_energy_env.split("#")
                        beast_id = int(beast_id_str)
                        energy = float(energy_str)
                        environment_str = str(environment_str)
                        await handle_beast_gone(
                            beast_id, energy, environment_str
                        )
                    case cmd.NO_BEASTS_LEFT_INFO:
                        await handle_no_beasts_left()
                    case cmd.SHUTDOWN_INFO:
                        break
            except websockets.ConnectionClosedError:
                print_and_flush("Connection closed by server")
                break
        await handle_shutdown()


def client_main():
    """
    Parse the command line and start the client loop with the appropriate
    arguments.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="User name for authentification")
    parser.add_argument(
        "password_file_name",
        help="Name of File containing Password for authentification.",
    )
    parser.add_argument(
        "-n", "--hostname", type=str, help="Host name", default="localhost"
    )
    parser.add_argument(
        "-p", "--port", type=int, help="Port number", default=9721
    )
    args = parser.parse_args()
    try:
        asyncio.run(
            client_loop(
                args.username,
                args.password_file_name,
                args.hostname,
                args.port,
            )
        )
    except ConnectionClosed:
        print_and_flush("Connection closed by server")


if __name__ == "__main__":
    client_main()

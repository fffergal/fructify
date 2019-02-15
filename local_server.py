import functools
import signal
import time
import threading
import wsgiref.simple_server

import passenger_wsgi


def stop_serving(app_server, old_sigint_handler, signalnum, frame):
    print("Stopping")
    app_server.shutdown()
    signal.signal(signal.SIGINT, old_sigint_handler)


def main():
    app_server = wsgiref.simple_server.make_server(
        "127.0.0.1",
        8000,
        passenger_wsgi.application,
    )
    old_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(
        signal.SIGINT, functools.partial(stop_serving, app_server, old_sigint_handler)
    )
    server_thread = threading.Thread(target=app_server.serve_forever) 
    print("Started on port 8000")
    server_thread.start()
    while server_thread.is_alive():
        time.sleep(0.4)
    app_server.server_close()
    print("Stopped")


if __name__ == "__main__":
    main()

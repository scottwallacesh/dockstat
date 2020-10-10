#!/usr/bin/env python3
"""
Module to act as a Prometheus Exporter for Docker containers with a
    healthcheck configured
"""

import argparse
import http.server
import os.path
import socketserver
import sys
import time

import docker

LISTEN_PORT = 8080
HEALTHY_STR = 'healthy'


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Class to encompass the requirements of a Prometheus Exporter
        for Docker containers with a healthcheck configured
    """
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method to handle GET requests
        """
        if self.path == '/metrics':
            self._metrics()

        if self.path == '/healthcheck':
            self._healthcheck()


    def _healthcheck(self, message=True):
        """
        Method to return 200 or 500 response and an optional message
        """
        if not healthy():
            self.send_response(500)
            self.end_headers()
            if message:
                self.wfile.write(b'ERR')
            return

        self.send_response(200)
        self.end_headers()
        if message:
            self.wfile.write(b'OK')


    def _metrics(self):
        """
        Method to handle the request for metrics
        """
        self._healthcheck(message=False)

        api = docker.APIClient()

        client = docker.from_env()
        for container in client.containers.list():
            now = int(round(time.time() * 1000))
            data = api.inspect_container(container.id)

            try:
                health_str = data["State"]["Health"]["Status"]
            except KeyError:
                pass
            else:
                self.wfile.write(
                    bytes(
                        f'container_inspect_state_health_status{{'
                        f'id="{container.id}",'
                        f'name="{container.name}",'
                        f'value="{health_str}"'
                        f'}} '
                        f'{int(health_str == HEALTHY_STR)} {now}\n'.encode()
                    )
                )


def healthy():
    """
    Simple funtion to return if all the requirements are met
    """
    return all([
        os.path.exists('/var/run/docker.sock'),
    ])


if __name__ == '__main__':
    def cli_parse():
        """
        Function to parse the CLI
        """
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-H', '--healthcheck',
            action='store_true',
            help='Simply exit with 0 for healthy or 1 when unhealthy',
        )

        return parser.parse_args()


    def main():
        """
        main()
        """
        args = cli_parse()

        if args.healthcheck:
            # Invert the sense of 'healthy' for Unix CLI usage
            return not healthy()

        Handler = SimpleHTTPRequestHandler

        with socketserver.TCPServer(('', LISTEN_PORT), Handler) as httpd:
            httpd.serve_forever()

        return True

    sys.exit(main())

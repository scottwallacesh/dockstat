#!/usr/bin/env python3
"""
Module to act as a Prometheus Exporter for Docker containers with a
    healthcheck configured
"""

import argparse
import os.path
import sys
from http.server import HTTPServer

import docker
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
    MetricsHandler,
)

LISTEN_PORT = 8080
HEALTHY_STR = 'healthy'


class HTTPHandler(MetricsHandler):
    """
    Class to encompass the requirements of a Prometheus Exporter
        for Docker containers with a healthcheck configured
    """

    def __init__(self, *args, **kwargs):
        self.docker_api = docker.APIClient()
        self.docker_client = docker.from_env()
        super().__init__(*args, **kwargs)

    # Override built-in method
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method to handle GET requests
        """
        if self.path == '/metrics':
            self._metrics()

        if self.path == '/healthcheck':
            if not healthy():
                print('ERROR: Check requirements')
                self._respond(500, 'ERR')

            self._respond(200, 'OK')

    def _respond(self, status, message):
        """
        Method to output a simple HTTP status and string to the client
        """
        self.send_response(int(status) or 500)
        self.end_headers()
        self.wfile.write(bytes(str(message).encode()))

    def _metrics(self):
        """
        Method to handle the request for metrics
        """
        if not healthy:
            print('ERROR: Check requirements')
            self._respond(500, 'Server not configured correctly')
            return

        registry = CollectorRegistry()

        gauge = Gauge(
            'container_inspect_state_health_status',
            "Container's healthcheck value (binary)",
            labelnames=['id', 'name', 'value'],
            registry=registry
        )

        for container in self.docker_client.containers.list():
            data = self.docker_api.inspect_container(container.id)

            try:
                health_str = data["State"]["Health"]["Status"]
                label_values = [
                    container.id,
                    container.name,
                    health_str,
                ]
            except KeyError:
                pass
            else:
                gauge.labels(*label_values).set(int(health_str == HEALTHY_STR))

        self._respond(200, generate_latest(registry).decode())


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

        print(f'Starting web server on port {LISTEN_PORT}')
        try:
            HTTPServer(('', LISTEN_PORT), HTTPHandler).serve_forever()
        except KeyboardInterrupt:
            print('Exiting')

        return 0

    sys.exit(main())

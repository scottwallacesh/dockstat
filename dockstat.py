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
        if not self._healthcheck(message=False):
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

        self.wfile.write(generate_latest(registry))


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

        HTTPServer(('', LISTEN_PORT), HTTPHandler).serve_forever()

        return 0

    sys.exit(main())

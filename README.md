[Prometheus](https://prometheus.io/) endpoint to report the healthcheck status of Docker containers.

# Usage
```
usage: dockstat.py [-h] [-H]

optional arguments:
  -h, --help         show this help message and exit
  -H, --healthcheck  Simply exit with 0 for healthy or 1 when unhealthy
```

# Example
```
curl -qsS localhost:8080/metrics
# HELP container_inspect_state_health_status Container's healthcheck value (binary)
# TYPE container_inspect_state_health_status gauge
container_inspect_state_health_status{id="21ac232f35edc4e630ed0c6b19b828a40df3dbc280c6bcf779b02a1488a741c3",name="alertify",value="healthy"} 1.0
container_inspect_state_health_status{id="73a3d19d996de90f15da6cea016d2b1733d0e63bca4d36b0a1bcb2d680d6f108",name="dockstat",value="healthy"} 1.0
container_inspect_state_health_status{id="db14abb41eec0ff06dc11b740b71839aec2b3855192b83a4ba31ee77bd21abfd",name="gotify",value="healthy"} 1.0
container_inspect_state_health_status{id="470e17a15751881cc0787f9aab6f1af000b7bbce7e590d82de987c583425b4ef",name="down-example",value="unhealthy"} 0.0
```

# Notes
* Requires access to the Docker socket (`/var/run/docker.sock`)

# Docker
## Build
```bash
docker build . -t 'dockstat:latest'
```

## Run
```bash
docker run --name dockstat -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock:ro -e TZ=Europe/London dockstat:latest
```

## Compose
```yaml
---
version: "2"
services:
  dockstat:
    image: dockstat:latest
    container_name: dockstat
    environment:
      - TZ=Europe/London
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
```

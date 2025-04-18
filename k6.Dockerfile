FROM grafana/k6:0.58.0

COPY code/ /usr/src/app/
WORKDIR /usr/src/app

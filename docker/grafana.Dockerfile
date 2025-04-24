FROM grafana/grafana:9.5.21
RUN grafana-cli plugins install blackmirror1-singlestat-math-panel
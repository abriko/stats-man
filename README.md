stats-mam
=============
监控URL状态生成报告

#### Usage
```
docker run --rm -it \
            -e WATCH_URLS="" \
            -e WATCH_INTERVAL=1 \
            -e OUT_DIR="/app/tmp" \
            stats-man
```

#### Devel

```
docker rm -f stats-man
docker run -it -p 3003:3000 \
            -v /opt/work/stats-man:/app \
            -v /opt:/opt \
            --name stats-man \
            python:3.11-bullseye bash


docker kill stats-man && docker start stats-man

docker attach stats-man


export WATCH_URLS="http://some-endpoint:8080/,http://some-endpoint2"
export WATCH_INTERVAL=""
export OUT_DIR="/opt/work/tmp"
python /app/app/main.py
```
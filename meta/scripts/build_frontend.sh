docker build \
    --platform linux/amd64 \
    -f meta/dockerfile/front.Dockerfile \
    -t ghcr.io/xiaozheyao/serving-front:dev . \
&& docker push ghcr.io/xiaozheyao/serving-front:dev

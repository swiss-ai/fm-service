cd apps/home \
&& docker build \
    --platform linux/amd64,linux/arm64 \
    -t ghcr.io/xiaozheyao/chat-front:dev . \
&& docker push ghcr.io/xiaozheyao/chat-front:dev

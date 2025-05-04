FROM node:lts AS runtime
WORKDIR /app

COPY apps/ .
COPY .env .
RUN npm install
RUN npm run build

ENV HOST=0.0.0.0
ENV PORT=4321
EXPOSE 4321
ENTRYPOINT ["node", "./dist/server/entry.mjs"]
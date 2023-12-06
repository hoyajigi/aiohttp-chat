FROM python:3.11-alpine
WORKDIR /app
ARG REDIS_HOST
ENV REDIS_HOST=redis
ARG REDIS_PORT
ENV REDIS_PORT=6379

COPY . /app
RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev
RUN pip install -r requirements.txt
CMD ["python", "aiohttp_chat/main.py"]

FROM python:3.12.3-slim

RUN apt update && apt install -y neovim && apt clean

WORKDIR /app

COPY  . .

CMD [ "python","main.py" ]

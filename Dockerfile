FROM python:3.12.3-slim

RUN apt update && apt install -y neovim && apt clean && pip install duckdb

WORKDIR /app

COPY  . .

CMD [ "python","main.py" ]

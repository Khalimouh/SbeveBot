FROM python:3.11.6-slim-bookworm

RUN pip install poetry==1.2.0
RUN apt update -y
RUN apt install opus-tools ffmpeg -y

COPY . /sbevebot

WORKDIR /sbevebot
RUN poetry install --without dev

ENTRYPOINT ["poetry", "run","python" ,"./sbevebot/steve.py", "./sbevebot/.env","1>","/dev/null"]

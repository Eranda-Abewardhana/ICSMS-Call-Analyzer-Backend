FROM python:3.10-slim

WORKDIR /code

EXPOSE 8000

COPY ./requirements.txt /code/requirements.txt

RUN pip --timeout=1000 install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app

RUN apt-get update && apt-get install -y ffmpeg

COPY ./.env /code/.env

COPY ./entrypoint.sh /code/entrypoint.sh

RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]

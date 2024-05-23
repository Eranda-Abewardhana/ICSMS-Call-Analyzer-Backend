FROM python:3.10-slim

WORKDIR code

EXPOSE 8000

COPY ./requirements.txt /code/requirements.txt

RUN pip --timeout=1000 install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app

RUN  apt update

RUN  apt install ffmpeg -y

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

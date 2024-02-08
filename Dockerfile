FROM python:3.8.18-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

CMD ["python", "./run.py", "-r"]
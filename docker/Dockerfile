FROM python:3.9.9

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

WORKDIR /testapp

RUN pip install --upgrade pip

RUN pip install fastapi uvicorn sample-helper-aws-appconfig

COPY docker/testapp.py .

COPY docker/run_uvicorn.sh .

EXPOSE 80

CMD ["./run_uvicorn.sh"]

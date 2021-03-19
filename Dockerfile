FROM python:3.8-alpine

WORKDIR /app

COPY ace-parser.py requirements.txt ./
RUN apk --no-cache add gcc python3-dev musl-dev && \
    pip install -r requirements.txt && \
    mkdir /app/out

CMD ["python", "ace-parser.py"]

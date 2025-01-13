FROM python:3.11-alpine

WORKDIR /app

RUN mkdir sender
RUN mkdir triger

COPY /sender /app/sender
COPY /triger /app/triger
COPY requirements.txt /app
COPY run.sh /app
COPY prod.env /app
RUN mv /app/prod.env /app/.env

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod a+x run.sh

CMD ["./run.sh"]
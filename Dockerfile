FROM python:3.11

WORKDIR /app

RUN mkdir sender
RUN mkdir triger

COPY /sender /app/sender
COPY /triger /app/triger
COPY requirements.txt /app
COPY .env /app
COPY run.sh /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod a+x run.sh

CMD ["./run.sh"]
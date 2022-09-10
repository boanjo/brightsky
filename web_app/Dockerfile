FROM python:3.6

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

RUN mkdir -p /app/templates && mkdir -p /app/static/images 
COPY templates/*.html /app/templates/
COPY static/images/* /app/static/images/
COPY static/* /app/static/
COPY config.json /app
COPY app.py /app
CMD python -u app.py

FROM python:3.13

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 5000

CMD ["python", "mma_events_web.py"]

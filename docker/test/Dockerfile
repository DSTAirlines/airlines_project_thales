FROM python:3.9
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["python", "cron_run.py"]
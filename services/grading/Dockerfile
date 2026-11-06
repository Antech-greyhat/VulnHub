FROM python:3.12-slim
WORKDIR /srv/grading
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV PORT=9000 PYTHONUNBUFFERED=1
EXPOSE 9000
CMD ["python", "app.py"]

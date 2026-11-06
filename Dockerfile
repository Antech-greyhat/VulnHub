FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash mfano

WORKDIR /srv/mfano/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x docker/entrypoint.sh \
    && mkdir -p /srv/mfano/data /srv/mfano/reports \
    && chown -R mfano:mfano /srv/mfano

USER mfano
ENV MFANO_HOME=/srv/mfano MFANO_BIND=0.0.0.0 MFANO_PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["docker/entrypoint.sh"]

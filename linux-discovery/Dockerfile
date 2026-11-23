FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y python3 file findutils less \
    && groupadd --gid 2200 teachers \
    && groupadd --gid 2201 archive \
    && useradd --uid 1100 --create-home --user-group --shell /bin/bash learner \
    && useradd --uid 1101 --create-home --gid teachers --shell /bin/bash teacher

COPY docs/.internal/maintainer/answer-key/linux_discovery.py /usr/local/lib/mfano/discovery.py
COPY linux-discovery/welcome.sh /home/learner/welcome.sh
COPY linux-discovery/README.md /home/learner/README.md

RUN chmod 0500 /usr/local/lib/mfano/discovery.py \
    && python3 -B /usr/local/lib/mfano/discovery.py prepare

USER learner
WORKDIR /practice
ENV PYTHONDONTWRITEBYTECODE=1 LC_ALL=C
CMD ["bash", "--rcfile", "/home/learner/welcome.sh", "-i"]

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y python3 sudo less \
    && groupadd --gid 2200 teachers \
    && groupadd --gid 2201 archive \
    && useradd --uid 1100 --create-home --user-group --groups teachers --shell /bin/bash learner \
    && useradd --uid 1101 --create-home --user-group --groups teachers --shell /bin/bash teacher \
    && useradd --uid 1102 --create-home --user-group --shell /bin/bash outsider \
    && useradd --uid 1103 --create-home --gid archive --shell /bin/bash archivist

COPY docs/.internal/maintainer/answer-key/linux_ownership.py /usr/local/lib/mfano/ownership.py
COPY linux-ownership/check-ownership /usr/local/bin/check-ownership
COPY linux-ownership/welcome.sh /home/learner/welcome.sh
COPY linux-ownership/README.md /home/learner/README.md

RUN chmod 0500 /usr/local/lib/mfano/ownership.py \
    && chmod 0755 /usr/local/bin/check-ownership \
    && printf '%s\n' 'learner ALL=(root) NOPASSWD: /usr/bin/chmod *, /usr/bin/chown *, /usr/bin/chgrp *, /usr/local/lib/mfano/ownership.py FO-*' > /etc/sudoers.d/mfano-practice \
    && chmod 0440 /etc/sudoers.d/mfano-practice \
    && visudo -cf /etc/sudoers.d/mfano-practice \
    && python3 -B /usr/local/lib/mfano/ownership.py prepare

USER learner
WORKDIR /practice
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["bash", "--rcfile", "/home/learner/welcome.sh", "-i"]

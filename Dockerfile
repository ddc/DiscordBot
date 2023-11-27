FROM python:3.12-slim-buster
LABEL Description="DiscordBot"

RUN mkdir -p /opt/DiscordBot
WORKDIR /opt/DiscordBot
ADD . /opt/DiscordBot

RUN apt-get update \
&& rm -rf /var/lib/apt/lists/* \
&& apt-get -y autoremove \
&& apt-get -y clean \

RUN python -m pip install --upgrade pip \
&& python -m pip install --no-cache-dir -r ./requirements.txt

CMD ["python", "bot.py"]

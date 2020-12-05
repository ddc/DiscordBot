FROM python:3.9.0
#################
LABEL Description="DiscordBot"
#################
RUN mkdir -p /opt/DiscordBot
WORKDIR /opt/DiscordBot
ADD . /opt/DiscordBot
RUN python -m pip install --upgrade pip \
&& python -m pip install --no-cache-dir -r ./requirements.txt
#################
CMD ["python", "launcher.py", "--start"]

FROM python:3.8.5
#################
LABEL Description="DiscordBot"
#################
RUN mkdir -p /opt/DiscordBot
WORKDIR /opt/DiscordBot
ADD . /opt/DiscordBot
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt
#################
CMD ["python", "launcher.py", "--start"]

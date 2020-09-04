FROM python
#################
LABEL Description="DiscordBot"
#################
ARG token
#################
RUN mkdir -p /opt/DiscordBot
WORKDIR /opt/DiscordBot
ADD . /opt/DiscordBot
RUN echo $token > ./config/token.txt
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt
#################
CMD ["python", "/opt/DiscordBot/launcher.py", "--start"]

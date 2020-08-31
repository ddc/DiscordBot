FROM python
#################
LABEL Description="DiscordBot"
#################
ARG token
#################
RUN apt-get -y update && apt-get -y upgrade
ADD . /opt/DiscordBot/
RUN echo $token > /opt/DiscordBot/config/token.txt
RUN pip install --upgrade pip
RUN pip install -r /opt/DiscordBot/requirements.txt
RUN apt-get install -y vim && apt-get -y clean && apt-get -y autoclean && apt-get -y autoremove
#################
CMD ["python", "/opt/DiscordBot/launcher.py", "--start"]

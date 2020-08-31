FROM python
#################
LABEL Description="DiscordBot"
#################
ARG token
#################
RUN apt-get -y update
ADD . /opt/DiscordBot/
RUN echo $token > /opt/DiscordBot/config/token.txt
RUN pip install -r /opt/DiscordBot/requirements/requirements.txt
RUN apt-get -y clean && apt-get -y autoclean && apt-get -y autoremove
#################
CMD ["python", "/opt/DiscordBot/launcher.py", "--start"]

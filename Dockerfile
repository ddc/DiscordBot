FROM python
#################
LABEL Description="DiscordBot"
#################
ARG token
#################
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y vim git && apt-get -y clean && apt-get -y autoclean && apt-get -y autoremove
RUN git clone https://github.com/ddc/DiscordBot.git /opt/DiscordBot
RUN echo $token > /opt/DiscordBot/config/token.txt
RUN pip install --upgrade pip
RUN pip install -r /opt/DiscordBot/requirements.txt
#################
CMD ["python", "/opt/DiscordBot/launcher.py", "--start"]

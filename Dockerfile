FROM python
#################
LABEL Description="DiscordBot"
#################
RUN apt-get -y update
ADD . /opt/DiscordBot/
RUN pip install -r /opt/DiscordBot/requirements/requirements.txt
RUN apt-get -y clean && apt-get -y autoclean && apt-get -y autoremove
#################
CMD ["python", "/opt/DiscordBot/launcher.py", "--start"]

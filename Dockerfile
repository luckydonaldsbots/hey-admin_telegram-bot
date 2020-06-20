FROM tiangolo/meinheld-gunicorn:python3.7

COPY $FOLDER/requirements.txt   /config/
RUN pip install --no-cache-dir -r /config/requirements.txt
RUN pip uninstall pytgbot -y && pip install -e git://github.com/luckydonald/pytgbot.git@109dc8bbd178a747a81325fa8b53a1c7f9511ea9#egg=pytgbot_109dc8b
COPY $FOLDER/code   /app

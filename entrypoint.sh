
# exec CMD

CMD="/usr/local/bin/uwsgi --ini /etc/uwsgi/uwsgi.ini --need-app --die-on-term --socket='/sockets/${URL_PATH}.sock' $@";

echo ">> exec docker CMD"
echo "$CMD"
exec "$CMD"



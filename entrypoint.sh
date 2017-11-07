#!/bin/bash
set -x;

chown -R $USER_UID:$GROUP_UID /sockets/bots/
CMD="/usr/local/bin/uwsgi";
ARGS="--ini /config/uwsgi.ini --need-app --die-on-term --socket=/sockets/bots/${URL_PATH}.sock $@";
echo "exec gosu $USER_UID:$GROUP_UID $CMD ''$ARGS''";
exec gosu $USER_UID:$GROUP_UID $CMD $ARGS

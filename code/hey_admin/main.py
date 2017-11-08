# -*- coding: utf-8 -*-
from flask import Flask, url_for
from luckydonaldUtils.logger import logging
from pytgbot import Bot
from pytgbot.api_types.receivable.peer import Chat, User
from pytgbot.api_types.receivable.updates import Message, Update
from teleflask.messages import MessageWithReplies, HTMLMessage, ForwardMessage

from .langs.en import Lang as LangEN
from .secrets import API_KEY, URL_HOSTNAME, URL_PATH
from luckydonaldUtils.exceptions import assert_type_or_raise
import re
from html import escape

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

from teleflask import Teleflask
app = Flask(__name__)

# sentry = add_error_reporting(app)
bot = Teleflask(API_KEY, hostname=URL_HOSTNAME, hostpath=URL_PATH, hookpath="/income/{API_KEY}")
bot.init_app(app)

assert_type_or_raise(bot.bot, Bot)
AT_ADMIN_REGEX = re.compile(".*([^\\w]|^)@admins?(\\W|$).*")


@app.errorhandler(404)
def url_404(error):
    from flask import request
    return "Nope. <br>Env: {request.environ!r}<br>Path: {request.full_path!r}<br>Url: {request.url}<br>Exception: {e}".format(request=request, e=error)
# end def

@app.route("/", methods=["GET","POST"])
def url_root():
    import os
    # return repr(os.environ)
    from flask import request
    return "Yep. <br>Env: {request.environ!r}<br>Path: {request.full_path!r}<br>Url: {request.url}".format(request=request)
# end def


@app.route('/bar', methods=["GET","POST"])
@app.route('/baz/', methods=["POST"])
def bar():
    from flask import request
    return "The URL for this page is {}<br><br>Env: {request.environ!r}<br>Path: {request.full_path!r}<br>Url: {request.url}<br>Method: {request.method}".format(url_for('bar'), request=request)
#  end if


@app.route("/holy_hacks/shit/<path:command>")
def do_shitty_stuff(command):
    from urllib.parse import unquote
    from html import escape
    try:
        return escape(repr(
            eval(unquote(command), {"app":app, "bot":bot})
            #False
        ))
    except Exception as e:
        return escape(repr(e))
    # end try
# end def


@bot.command("start")
def cmd_start(update, text):
    return "test."
# end def


@bot.command("help")
def cmd_start(update, text):
    return "test."
# end def


@bot.command("admin")
@bot.command("admins")
def cmd_admins(update, text):
    return update_call_admins(update.message)
# end def


@bot.on_message("text")
def msg_text(update, msg):
    assert isinstance(update.message, Message)
    if AT_ADMIN_REGEX.search(update.message.text):
        return update_call_admins(update.message)
    # end if
# end def


@bot.on_message("caption")
def msg_caption(update, msg):
    assert isinstance(update.message, Message)
    if AT_ADMIN_REGEX.search(update.message.caption):
        return update_call_admins(update.message)
    # end if
# end def


def update_call_admins(message):
    """
    :param message: The message from inside the update.
    :type  message: Message
    :rtype: None
    """
    assert isinstance(bot.bot, Bot)
    assert isinstance(message, Message)
    assert isinstance(message.chat, Chat)
    assert isinstance(message.chat.id, int)
    chat_id = message.chat.id

    # prepare the messages
    msgs = []
    msgs.append(HTMLMessage(LangEN.admin_message_info.format(user=format_user(message.from_peer), chat=message.chat)))
    msgs.append(ForwardMessage(message.message_id, chat_id))
    if message.reply_to_message:
        msgs.append(HTMLMessage(LangEN.admin_reply_info.format(user=format_user(message.reply_to_message.from_peer))))
        msgs.append(ForwardMessage(message.reply_to_message.message_id, chat_id))
    # end if
    batch = MessageWithReplies(*msgs)

    # notify each admin
    admins = bot.bot.get_chat_administrators(chat_id)
    for admin in admins:
        batch.send(bot.bot, admin.user.id, reply_id=None)
    # end for
# end def


def format_user(peer):
    assert isinstance(peer, User)
    name = (str(peer.first_name) + " " + str(peer.last_name)).strip()
    if name:
        name = '<b>{name}</b> '.format(name=escape(name))
    else:
        name = ''
    # end if
    username = ("@" + str(peer.username).strip() + " ") if peer.username else ""
    return '{name}{username}<a href="tg://user?id={id}">{id}</a>'.format(name=name, username=username, id=peer.id)
# end if


def format_chat(chat, msg_id):
    assert isinstance(chat, Chat)
    assert isinstance(bot.bot, Bot)

    invite_link = chat.invite_link
    try:
        invite_link = bot.bot.export_chat_invite_link(chat.id)
    except:
        pass
    # end try
    try:
        chat = bot.bot.get_chat(chat.id)
        invite_link = chat.invite_link
    except:
        pass
    # end if
    if chat.title:
        title = "<b>{title}</b>".format(title=escape(chat.title))
    else:
        title = "<i>{untitled_chat}</i>".format(untitled_chat=LangEN.untitled_chat)
    # end if
    if chat.username:
        return '{title} <a href="t.me/{username}/{msg_id}">{chat_id}</a>'.format(
            username=chat.username, msg_id=msg_id, title=title, chat_id=chat.id
        )
    elif invite_link:
        return '{title} <a href="{invite_link}">{chat_id}</a>'.format(
            title=title, invite_link=invite_link, chat_id=chat.id
        )
    else:
        return '{title} <code>{chat_id}</code>'.format(title=title, chat_id=chat.id)
    # end if
# end def




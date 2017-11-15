# -*- coding: utf-8 -*-
from flask import Flask, url_for
from luckydonaldUtils.logger import logging
from pytgbot import Bot
from pytgbot.api_types.receivable.peer import Chat, User
from pytgbot.api_types.receivable.updates import Message, Update
from pytgbot.exceptions import TgApiServerException, TgApiException
from teleflask.messages import MessageWithReplies, HTMLMessage, ForwardMessage
from requests import RequestException

from .langs.en import Lang as LangEN
from .secrets import API_KEY, URL_HOSTNAME, URL_PATH
from luckydonaldUtils.exceptions import assert_type_or_raise
import re
from html import escape

POSSIBLE_CHAT_TYPES = ("supergroup", "group", "channel")
SEND_BACKOFF = 5

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)

from teleflask import Teleflask
app = Flask(__name__)

# sentry = add_error_reporting(app)
bot = Teleflask(API_KEY, hostname=URL_HOSTNAME, hostpath=URL_PATH, hookpath="/income/{API_KEY}")
bot.init_app(app)

assert_type_or_raise(bot.bot, Bot)
AT_ADMIN_REGEX = re.compile(".*([^\\w]|^)@(admins?|{bot})(\\W|$).*".format(bot=bot.username))


@app.errorhandler(404)
def url_404(error):
    return "Nope.", 404
# end def


@app.route("/", methods=["GET","POST"])
def url_root():
    return "Yep."
# end def


@app.route("/test", methods=["GET","POST"])
def url_test():
    return "Success", 200
# end def


@app.route("/holy_hacks/shit/<path:command>")
def do_shitty_stuff(command):
    from urllib.parse import unquote
    from html import escape
    try:
        return escape(repr(
            #eval(unquote(command), {"app":app, "bot":bot})
            False
        ))
    except Exception as e:
        return escape(repr(e))
    # end try
# end def


@bot.command("start")
def cmd_start(update, text):
    return HTMLMessage(LangEN.help_message)
# end def


@bot.command("help")
def cmd_start(update, text):
    return HTMLMessage(LangEN.help_message)
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

    # only do it in groups
    if message.chat.type not in POSSIBLE_CHAT_TYPES:
        logger.debug("Discarding message (has no admins): {}".format(message))
        return
    # end def

    # prepare the messages
    msgs = []
    chat = format_chat(message)
    user = format_user(message.from_peer)
    logger.debug("user: " + repr(user))
    logger.debug("chat: " + repr(chat))
    if message.reply_to_message:
        # is reply
        if message.reply_to_message.from_peer.id == message.from_peer.id:
            # same user
            text = LangEN.admin_reply_info_same.format(user=user, chat=chat)

        else:
            # different user
            text = LangEN.admin_reply_info.format(
                user=user, chat=chat, reply_user=format_user(message.reply_to_message.from_peer)
            )
        # end if
        msgs.append(HTMLMessage(text + (LangEN.unstable_text if bot.username == "hey_admin_bot" else "")))
        msgs.append(ForwardMessage(message.reply_to_message.message_id, chat_id))
    else:
        # isn't reply
        msgs.append(HTMLMessage(LangEN.admin_message_info.format(user=user, chat=chat) + (LangEN.unstable_text if bot.username == "hey_admin_bot" else "")))
    # end if
    msgs.append(ForwardMessage(message.message_id, chat_id))
    batch = MessageWithReplies(*msgs)

    # notify each admin
    try:
        admins = bot.bot.get_chat_administrators(chat_id)
    except TgApiServerException as e:
        if "there is no administrators in the private chat" in e.description:
            return "There is no administrators in the private chat"
        # end if
        raise e
    # end try
    failed_admins = []
    for admin in admins:
        if admin.user.is_bot:
            continue  # can't send messages to bots
        # end if
        for backoff in range(SEND_BACKOFF):
            try:
                batch.send(bot.bot, admin.user.id, reply_id=None)
                break
            except TgApiServerException as e:
                logger.info("Server Exception. Aborting.", exc_info=True)
                if "bot can't initiate conversation with a user" in e.description:
                    failed_admins.append(admin)
                # end if
                break
            except (TgApiException, RequestException) as e:
                logger.exception("Unknown Exception. Retrying.")
            # end if
        else:
            # backoff exceeded
            logger.debug("Admin failed: {}".format(format_user(admin.user)))
        # end for
    # end for
    if len(failed_admins) == 0:
        return
    elif len(failed_admins) == 1:
        return HTMLMessage(LangEN.couldnt_contact_singular(admin=format_user(failed_admins[0].user), num=len(admins), bot=bot.username, chat_id=chat_id))
    else:
        return HTMLMessage(LangEN.couldnt_contact_plural([format_user(admin.user) for admin in failed_admins], num=len(admins), bot=bot.username, chat_id=chat_id))
    # end if
# end def


def format_user(peer):
    assert isinstance(peer, User)
    name = (str(peer.first_name) if peer.first_name else "" + " " + str(peer.last_name)).strip() if peer.last_name else ""
    if name:
        name = '<b>{name}</b> '.format(name=escape(name))
    else:
        name = ''
    # end if
    username = ('<a href="t.me/{username}">@{username}</a> '.format(username=str(peer.username).strip())) if peer.username else ""
    return '{name}{username}(<a href="tg://user?id={id}">{id}</a>)'.format(name=name, username=username, id=peer.id)
# end if


def format_chat(message):
    chat, msg_id = message.chat, message.message_id
    assert isinstance(chat, Chat)
    assert isinstance(bot.bot, Bot)
    logger.info(repr(message))
    if chat.title:
        title = "<b>{title}</b>".format(title=escape(chat.title))
    else:
        title = "<i>{untitled_chat}</i>".format(untitled_chat=LangEN.untitled_chat)
    # end if
    if chat.username:
        return '{title} <a href="t.me/{username}/{msg_id}">@{username}</a>'.format(
            username=chat.username, msg_id=msg_id, title=title, chat_id=chat.id
        )
    # end if

    # try getting an invite link.
    invite_link = chat.invite_link
    if chat.type in ("supergroup", "channel") and not invite_link:
        try:
            invite_link = bot.bot.export_chat_invite_link(chat.id)
        except:
            logger.exception("export_chat_invite_link Exception.")
        # end try
    try:
        chat = bot.bot.get_chat(chat.id)
        invite_link = chat.invite_link
    except:
        pass
        # end if
    if invite_link:
        return '{title} (<a href="{invite_link}">{chat_id}</a>)'.format(
            title=title, invite_link=invite_link, chat_id=chat.id
        )
    else:
        return '{title} (<code>{chat_id}</code>)'.format(title=title, chat_id=chat.id)
    # end if
# end def


@bot.on_message("new_chat_members")
def on_join(update, message):
    assert_type_or_raise(message.new_chat_members, list)
    if bot.user_id not in [user.id for user in message.new_chat_members if isinstance(user, User)]:
        # not we were added
        return
    # end if

    return HTMLMessage(LangEN.join_message.format(bot=bot.username, chat_id=message.chat.id) + (LangEN.unstable_text if bot.username == "hey_admin_bot" else ""))
#end def



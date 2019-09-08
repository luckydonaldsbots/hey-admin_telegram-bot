# -*- coding: utf-8 -*-
import re
import random

from html import escape
from flask import Flask, jsonify
from pytgbot import Bot
from requests import RequestException
from teleflask import Teleflask
from pytgbot.exceptions import TgApiServerException, TgApiException
from teleflask.messages import MessageWithReplies, HTMLMessage, ForwardMessage
from luckydonaldUtils.logger import logging
from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.tg_bots.gitinfo import version_bp, version_tbp
from pytgbot.api_types.receivable.peer import Chat, User
from pytgbot.api_types.receivable.updates import Message

from .number_utils import from_supergroup
from .langs.en import Lang as LangEN
from .secrets import API_KEY, URL_HOSTNAME, URL_PATH


__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)

POSSIBLE_CHAT_TYPES = ("supergroup", "group", "channel")
SEND_BACKOFF = 5


app = Flask(__name__)
app.register_blueprint(version_bp)
# sentry = add_error_reporting(app)

bot = Teleflask(API_KEY, hostname=URL_HOSTNAME, hostpath=URL_PATH, hookpath="/income/{API_KEY}")
bot.init_app(app)
bot.register_tblueprint(version_tbp)

assert_type_or_raise(bot.bot, Bot)
AT_ADMIN_REGEX = re.compile(".*([^\\w]|^)@(admins?)(\\W|$).*")


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

@app.route("/healthcheck")
def url_healthcheck():
    """
    Checks if telegram api works.
    :return:
    """
    status = {}

    try:
        me = bot.bot.get_me()
        assert isinstance(me, User)
        logger.info(me)
        status['telegram api'] = True
    except Exception as e:
        logger.exception("Telegram API failed.")
        status['telegram api'] = False
    # end try

    success = all(x for x in status.values())
    return jsonify(status), 200 if success else 500
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
        logger.debug("Discarding message (not a chat type with admins): {}".format(message))
        return
    # end def

    # prepare the messages
    msgs = []
    chat = format_chat(message)
    user = format_user(message.from_peer)
    link = format_message_permalink(message)

    logger.debug("user: " + repr(user))
    logger.debug("chat: " + repr(chat))
    if message.reply_to_message:
        # is reply
        if message.reply_to_message.from_peer.id == message.from_peer.id:
            # same user
            text = LangEN.admin_reply_info_same.format(user=user, chat=chat, msg_link=link)

        else:
            # different user
            text = LangEN.admin_reply_info.format(
                user=user, chat=chat, reply_user=format_user(message.reply_to_message.from_peer), msg_link=link
            )
        # end if
        msgs.append(HTMLMessage(text + (LangEN.unstable_text if bot.username == "hey_admin_bot" else "")))
        msgs.append(ForwardMessage(message.reply_to_message.message_id, chat_id))
    else:
        # isn't reply
        msgs.append(HTMLMessage(LangEN.admin_message_info.format(user=user, chat=chat, msg_link=link) + (LangEN.unstable_text if bot.username == "hey_admin_bot" else "")))
    # end if
    msgs.append(ForwardMessage(message.message_id, chat_id))
    batch = MessageWithReplies(*msgs)
    batch.reply_id = None

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
    random.shuffle(admins)
    for admin in admins:
        admin_formatted = format_user(admin.user)
        logger.debug(f"Found admin {admin_formatted}: {admin.user!s}.")
        if admin.user.is_bot:
            logger.debug("Skipping admin, is bot.")
            continue  # can't send messages to bots
        # end if
        for backoff in range(SEND_BACKOFF):
            logger.debug(f"Sending from {chat_id} to {admin.user.id} {admin_formatted!s} (old: {batch.receiver!r}). Try {backoff + 1}/{SEND_BACKOFF}.")
            batch.receiver = admin.user.id
            batch.top_message.receiver = admin.user.id
            for reply in batch.reply_messages:
                reply.receiver = admin.user.id
            # end def

            try:
                batch.send(bot.bot)
                logger.debug(f"Sending to admin {admin_formatted!s}")
                break
            except TgApiServerException as e:
                logger.info("Server Exception. Aborting.")
                if "bot can't initiate conversation with a user" in e.description:
                    logger.debug("Can't contact admin, not started.")
                    failed_admins.append(admin)
                else:
                    logger.warn('sending to admin failed', exc_info=True)
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
    logger.debug("That's all the admins.")
    if len(failed_admins) == 0:
        logger.debug("Sent to all admins are successfully.")
        return
    elif len(failed_admins) == 1:
        logger.debug("Sent to all admins but one.")
        return HTMLMessage(LangEN.couldnt_contact_singular(admin=format_user(failed_admins[0].user), num=len(admins), bot=bot.username, chat_id=chat_id))
    else:
        logger.debug(f"Sent to all admins but {failed_admins}.")
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


def format_message_permalink(msg: Message) -> str:
    # we'll build the short chat_id from the long one.
    # supergroup are prefixed with -100, channels are just negative. Private messages are positive.
    short_chat_id = msg.from_peer.id
    if -1002147483647 <= short_chat_id < -1000000000000:
        short_chat_id = from_supergroup(short_chat_id)  # removes leading -100
    elif -2147483647 <= short_chat_id < 0:
        short_chat_id = -1 * short_chat_id
    # end if
    return f"https://t.me/c/{short_chat_id}/{msg.message_id}"
# end def


def format_chat(message: Message):
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

    # get updated chat information, i.e. also includes chat.invite_link
    if not chat.username and not chat.invite_link:
        try:
            chat = bot.bot.get_chat(chat.id)
        except:
            logger.warn("Could not (re)load chat info.", exc_info=True)
        # end try
    # end if

    # try generating an invite link.
    invite_link = chat.invite_link
    if chat.type in ("supergroup", "channel") and not invite_link:
        try:
            invite_link = bot.bot.export_chat_invite_link(chat.id)
        except:
            logger.warn("export_chat_invite_link Exception.", exc_info=True)
        # end try
    # end try

    if invite_link:
        return '{title} (<a href="{invite_link}">(Join))</a>)'.format(
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

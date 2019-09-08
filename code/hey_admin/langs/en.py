
class Lang(object):
    lang = "en"
    admin_message_info = 'You were <a href="{msg_link!s}">requested</a> in chat {chat} by user {user}:'
    admin_reply_info = 'In chat {chat} for the message</a> by {reply_user} the user {user} <a href="{msg_link!s}">requested</a> you:'
    admin_reply_info_same = 'You were <a href="{msg_link!s}">requested</a> in chat {chat} by user {user} about his own message. Strange.'
    untitled_chat = "Untitled chat"
    help_message = "This bot is will help users call out for all chat admins, " \
                   "simply by mentioning <code>@admin</code> or <code>@admins</code>."
    join_message = 'Oh, hey there.\nI will help contacting the @admins of this group. The admins just have to <a href="https://t.me/{bot}?start=join_{chat_id}">allow me</a> contacting them.'
    unstable_text = "\n\nNote, this is the unstable test version of @HeyAdminBot. Use that one instead. Or else!"
    couldnt_contact_singular = lambda admin, num, bot, chat_id: "Couldn't directly contact the admin {admin} of {num} admin{plural_s}.\nI need to be <a href=\"https://t.me/{bot}?start=join_{chat_id}\">started</a> by that admin first.".format(admin=admin, num=num, plural_s="s" if num != 0 else "", bot=bot, chat_id=chat_id)
    couldnt_contact_plural = lambda admins, num, bot, chat_id: "Couldn't directly contact the admins " + ", ".join(admins[:-1]) + " and " + admins[-1] + " of " + repr(num) + " admin" + ("s" if num != 0 else "") + ".\nI need to be <a href=\"https://t.me/" + bot + "?start=join_" + str(chat_id) + "\">started</a> by them fist."
# end class


class Lang(object):
    lang = "en"
    admin_message_info = "You were requested in chat {chat} by user {user}:"
    admin_reply_info = "In chat {chat} for the message by {reply_user} the user {user} requested you:"
    admin_reply_info_same = "You were requested in chat {chat} by user {user} about his own message. Strange."
    untitled_chat = "Untitled chat"
    help_message = "This bot is will help users call out for all chat admins, " \
                   "simply by mentioning <code>@admin</code> or <code>@admins</code>."
    join_message = 'Oh, hey there.\nI will help contacting the @admins of this group. The admins just have to <a href="https://t.me/{bot}?start=join_{chat_id}">allow me</a> contacting them.'
    unstable_text = "\n\nNote, this is the unstable test version of @HeyAdminBot. You shouldn't use it. Or else!"
# end class

import html

from telegram import ParseMode, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from EmikoRobot import DRAGONS, dispatcher
from EmikoRobot.modules.disable import DisableAbleCommandHandler
from EmikoRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
    ADMIN_CACHE,
)

from EmikoRobot.modules.helper_funcs.admin_rights import user_can_changeinfo, user_can_promote
from EmikoRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from EmikoRobot import SUPPORT_CHAT
from EmikoRobot.modules.log_channel import loggable
from EmikoRobot.modules.helper_funcs.alternate import send_message


@bot_admin
@user_admin
def set_sticker(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("You're missing rights to change chat info!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Anda perlu membalas beberapa stiker untuk mengatur set stiker obrolan!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(f"Berhasil mengatur stiker grup baru di {chat.title}!")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Maaf, karena pembatasan telegram, obrolan harus memiliki minimal 100 anggota sebelum mereka dapat memiliki stiker grup!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text("Anda perlu membalas beberapa stiker untuk mengatur set stiker obrolan!")
       
    
@bot_admin
@user_admin
def setchatpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda kehilangan hak untuk mengubah info grup!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Anda hanya dapat mengatur beberapa foto sebagai foto obrolan!")
            return
        dlmsg = msg.reply_text("Just a sec...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Berhasil mengatur chatpic baru!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Balas beberapa foto atau file untuk mengatur foto obrolan baru!")
        
@bot_admin
@user_admin
def rmchatpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak yang cukup untuk menghapus foto grup")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Berhasil menghapus foto profil chat!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return
    
@bot_admin
@user_admin
def set_desc(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda kehilangan hak untuk mengubah info obrolan!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Mengatur deskripsi kosong tidak akan melakukan apa-apa!")
    try:
        if len(desc) > 255:
            return msg.reply_text("Deskripsi harus di bawah 255 karakter!")
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(f"Berhasil memperbarui deskripsi obrolan di {chat.title}!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")        
        
@bot_admin
@user_admin
def setchat_title(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak yang cukup untuk mengubah info obrolan!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Masukkan beberapa teks untuk mengatur judul baru di obrolan Anda!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Successfully set <b>{title}</b> as new chat title!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return
        
        
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("Anda tidak memiliki hak yang diperlukan untuk melakukan itu!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Anda tampaknya tidak mengacu pada pengguna atau ID yang ditentukan salah...",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ('administrator', 'creator'):
        message.reply_text("Dia Sudah Menjadi Admin, Tidak perlu melakukannya lagi!")
        return

    if user_id == bot.id:
        message.reply_text("Saya tidak bisa mempromosikan diri sendiri! Minta admin untuk melakukannya untuk saya.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("Saya tidak bisa mempromosikan seseorang yang tidak ada dalam grup.")
        else:
            message.reply_text("An error occured while promoting.")
        return

    bot.sendMessage(
        chat.id,
        f"Promoting a user in <b>{chat.title}</b>\n\nUser: {mention_html(user_member.user.id, user_member.user.first_name)}\nAdmin: {mention_html(user.id, user.first_name)}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def lowpromote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("Anda tidak memiliki hak yang diperlukan untuk melakukan itu!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Anda tampaknya tidak mengacu pada pengguna atau ID yang ditentukan tidak benar..",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ('administrator', 'creator'):
        message.reply_text("Dia Sudah Menjadi Admin, Tidak perlu melakukannya lagi!")
        return

    if user_id == bot.id:
        message.reply_text("Saya tidak bisa mempromosikan diri saya sendiri! Minta admin untuk melakukannya untuk saya.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("Saya tidak bisa mempromosikan seseorang yang tidak ada dalam grup.")
        else:
            message.reply_text("An error occured while promoting.")
        return

    bot.sendMessage(
        chat.id,
        f"Lowpromoting a user in <b>{chat.title}<b>\n\nUser: {mention_html(user_member.user.id, user_member.user.first_name)}\nAdmin: {mention_html(user.id, user.first_name)}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#LOWPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def fullpromote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Anda tampaknya tidak mengacu pada pengguna atau ID yang ditentukan tidak benar..",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ('administrator', 'creator'):
        message.reply_text("Bagaimana saya bisa mempromosikan seseorang yang sudah menjadi admin?")
        return

    if user_id == bot.id:
        message.reply_text("Saya tidak bisa mempromosikan diri saya sendiri! Minta admin untuk melakukannya untuk saya.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("Saya tidak bisa mempromosikan seseorang yang tidak ada dalam grup.")
        else:
            message.reply_text("Timbul galat saat promosi.")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "Demote", callback_data="demote_({})".format(user_member.user.id))
    ]])

    bot.sendMessage(
        chat.id,
        f"Fullpromoting a user in <b>{chat.title}</b>\n\n<b>User: {mention_html(user_member.user.id, user_member.user.first_name)}</b>\n<b>Promoter: {mention_html(user.id, user.first_name)}</b>",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#FULLPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("Orang ini MEMBUAT obrolan, bagaimana cara menurunkannya?")
        return

    if not user_member.status == "administrator":
        message.reply_text("Tidak bisa menurunkan apa yang tidak dipromosikan!")
        return

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
        )

        bot.sendMessage(
            chat.id,
            f"Sucessfully demoted a admins in <b>{chat.title}</b>\n\nAdmin: <b>{mention_html(user_member.user.id, user_member.user.first_name)}</b>\nDemoter: {mention_html(user.id, user.first_name)}",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "Could not demote. I might not be admin, or the admin status was appointed by another"
            " user, so I can't act upon them!",
        )
        return


@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("✅ Cache admin disegarkan!")


@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "Anda tampaknya tidak mengacu pada pengguna atau ID yang ditentukan tidak benar..",
        )
        return

    if user_member.status == "creator":
        message.reply_text(
           "This person CREATED the chat, how can i set custom title for him?",
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "Tidak dapat mengatur judul untuk non-admin!nPromote mereka terlebih dahulu untuk mengatur judul kustom!",
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "Aku tidak bisa mengatur gelarku sendiri! Dapatkan orang yang membuat saya admin untuk melakukannya untuk saya.",
        )
        return

    if not title:
        message.reply_text("Mengatur judul kosong tidak melakukan apa-apa!")
        return

    if len(title) > 16:
        message.reply_text(
            "Panjang judul lebih panjang dari 16 karakter.nTruncating menjadi 16 karakter.",
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text(
            "Entah mereka tidak dipromosikan oleh saya atau Anda menetapkan teks judul yang tidak mungkin diatur."
        )
        return

    bot.sendMessage(
        chat.id,
        f"Sucessfully set title for <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        msg.reply_text("Balas pesan untuk menyematkannya!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            msg.reply_text(
                f"Saya telah menyematkan pesan.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "👉 Buka pesan", url=f"{message_link}")
                        ]
                    ]
                ), 
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"MESSAGE-PINNED-SUCCESSFULLY\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    unpinner = chat.get_member(user.id)

    if (
        not (unpinner.can_pin_messages or unpinner.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("Anda tidak memiliki hak yang diperlukan untuk melakukan itu!")
        return

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message and is_group:
        try:
            context.bot.unpinChatMessage(
                chat.id, prev_message.message_id
            )
            msg.reply_text(
                f"Unpinned <a href='{message_link}'>this message</a>.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

    if not prev_message and is_group:
        try:
            context.bot.unpinChatMessage(chat.id)
            msg.reply_text(
                "Unpinned pesan yang disematkan terakhir."
            )
        except BadRequest as excp:
            if excp.message == "Message to unpin not found":
               msg.reply_text(
                   "Saya tidak dapat melihat pesan yang disematkan, Mungkin sudah tidak dipindah, atau menyematkan Pesan ke pesan lama 🙂"
               )
            else:
                raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"MESSAGE-UNPINNED-SUCCESSFULLY\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@bot_admin
def pinned(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    msg = update.effective_message
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        if msg.chat.username:
            link_chat_id = msg.chat.username
            message_link = f"https://t.me/{link_chat_id}/{pinned_id}"
        elif (str(msg.chat.id)).startswith("-100"):
            link_chat_id = (str(msg.chat.id)).replace("-100", "")
            message_link = f"https://t.me/c/{link_chat_id}/{pinned_id}"

        msg.reply_text(
            f'🔽 Pinned on {html.escape(chat.title)}.',
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="👉 Go to message", url=f"https://t.me/{link_chat_id}/{pinned_id}")]]
            ),
        )

    else:
        msg.reply_text(
            f"There is no pinned message in <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "Saya tidak memiliki akses ke tautan undangan, coba ubah izin saya!",
            )
    else:
        update.effective_message.reply_text(
            "Saya hanya bisa memberi Anda tautan undangan untuk supergrup dan saluran, maaf!",
        )


@connection_status
def adminlist(update, context):
    chat = update.effective_chat  # type: Optional[Chat] -> unused variable
    user = update.effective_user  # type: Optional[User]
    args = context.args  # -> unused variable
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message, "This command only works in Groups.")
        return

    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title  # -> unused variable

    try:
        msg = update.effective_message.reply_text(
            "Fetching group admins...",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "Fetching group admins...",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    administrators = bot.getChatAdministrators(chat_id)
    text = "Admins in <b>{}</b>:".format(html.escape(update.effective_chat.title))

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )

        if user.is_bot:
            administrators.remove(admin)
            continue

        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n 🌏 Creator:"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n🌟 Admin:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Akun Terhapus"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )
        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0],
                html.escape(admin_group),
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


@bot_admin
@can_promote
@user_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    bot: Optional[Bot] = context.bot
    match = re.match(r"demote_\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        member = chat.get_member(user_id)
        bot_member = chat.get_member(bot.id)
        bot_permissions = promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )                
        demoted = bot.promoteChatMember(
                      chat.id,
                      user_id,
                      can_change_info=False,
                      can_post_messages=False,
                      can_edit_messages=False,
                      can_delete_messages=False,
                      can_invite_users=False,
                      can_restrict_members=False,
                      can_pin_messages=False,
                      can_promote_members=False,
                      can_manage_voice_chats=False,
        )
        if demoted:
        	update.effective_message.edit_text(
        	    f"Admin {mention_html(user.id, user.first_name)} Demoted {mention_html(member.user.id, member.user.first_name)}!",
        	    parse_mode=ParseMode.HTML,
        	)
        	query.answer("Demoted!")
        	return (
                    f"<b>{html.escape(chat.title)}:</b>\n" 
                    f"#DEMOTE\n" 
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
                )
    else:
        update.effective_message.edit_text(
            "Pengguna ini tidak dipromosikan atau telah meninggalkan grup!"
        )
        return ""


@connection_status
def bug_reporting(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    bot = dispatcher.bot
    invitelink = bot.exportChatInviteLink(chat.id)
    puki = msg.text.split(None, 1)
    if len(puki) >= 2:
        bugnya = puki[1]
    else:
        msg.reply_text(
            "❌ <b>Anda harus menentukan bug yang akan dilaporkan.</b>\n • contoh: <code>/bug Music not working.</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        if len(bugnya) > 100:
            return msg.reply_text("Bug must needs to be under 100 characters!")
        bot.sendMessage(
            chat.id,
            f"✅ Bug Anda dikirimkan ke <b>Admin Bot</b>. Terima kasih telah melaporkan bugnya.",
            parse_mode=ParseMode.HTML,
        )
        if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
            try:
                bot.sendMessage(
                    f"@{SUPPORT_CHAT}",
                    f"📣 <b>New bug reported.</b>\n\n<b>Chat:</b> <a href='{invitelink}'>{chat.title}</a>\n<b>Name:</b> <a href='tg://user?id={msg.from_user.id}'>{mention_html(msg.from_user.id, msg.from_user.first_name)}</a>\n<b>User ID:</b> <code>{msg.from_user.id}</code>\n<b>Chat id:</b> <code>{chat.id}</code>\n\nContent of the report:\n{bugnya}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Go To Mesaage", url=f"{msg.link}")]]
                    ),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except Unauthorized:
                LOGGER.warning(
                    "Bot tidak dapat mengirim pesan ke support_chat, pergi dan periksa!"
                )
            except BadRequest as e:
                LOGGER.warning(e.message)
    except BadRequest:
        pass


__help__ = """
*Perintah Pengguna*:
❏ /admins*:* daftar admin di chat
❏ /pinned*:* untuk mendapatkan pesan yang disematkan saat ini.

*Perintah Berikut hanya Admin:*
❏ /pin*:* diam-diam menyematkan pesan yang dibalas - tambahkan `'keras'` atau `'beri tahu'` untuk memberikan pemberitahuan kepada pengguna
❏ /unpin*:* melepas pin pesan yang saat ini disematkan
❏ /invitelink*:* mendapat tautan undangan
❏ /promote*:* mempromosikan pengguna yang dibalas
❏ /fullpromote*:* mempromosikan pengguna yang dibalas dengan hak penuh
❏ /demote*:* menurunkan pengguna yang dibalas
❏ /title <title here>*:* menetapkan judul khusus untuk admin yang dipromosikan bot
❏ /admincache*:* paksa refresh daftar admin
❏ /del*:* menghapus pesan yang Anda balas
❏ /purge*:* menghapus semua pesan antara ini dan pesan yang dibalas.
❏ /purge <integer X>*:* menghapus pesan yang dibalas, dan X pesan yang mengikutinya jika membalas pesan.
❏ /setgtitle <text>*:* setel judul grup
❏ /setgpic*:* membalas gambar untuk ditetapkan sebagai foto grup
❏ /setdesc*:* Setel deskripsi grup
❏ /setsticker*:* Setel stiker grup

*Aturan*:
❏ /rules*:* dapatkan aturan untuk chat ini.
❏ /setrules <aturan Anda di sini>*:* tetapkan aturan untuk obrolan ini.
❏ /clearrules*:* hapus aturan chat ini.
"""

SET_DESC_HANDLER = CommandHandler("setdesc", set_desc, filters=Filters.chat_type.groups, run_async=True)
SET_STICKER_HANDLER = CommandHandler("setsticker", set_sticker, filters=Filters.chat_type.groups, run_async=True)
SETCHATPIC_HANDLER = CommandHandler("setgpic", setchatpic, filters=Filters.chat_type.groups, run_async=True)
RMCHATPIC_HANDLER = CommandHandler("delgpic", rmchatpic, filters=Filters.chat_type.groups, run_async=True)
SETCHAT_TITLE_HANDLER = CommandHandler("setgtitle", setchat_title, filters=Filters.chat_type.groups, run_async=True)

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist, run_async=True)
BUG_HANDLER = DisableAbleCommandHandler("bug", bug_reporting, run_async=True)

PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.chat_type.groups, run_async=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.chat_type.groups, run_async=True)
PINNED_HANDLER = CommandHandler("pinned", pinned, filters=Filters.chat_type.groups, run_async=True)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite, run_async=True)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, run_async=True)
FULLPROMOTE_HANDLER = DisableAbleCommandHandler("fullpromote", fullpromote, run_async=True)
LOW_PROMOTE_HANDLER = DisableAbleCommandHandler("lowpromote", lowpromote, run_async=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, run_async=True)

SET_TITLE_HANDLER = CommandHandler("title", set_title, run_async=True)
ADMIN_REFRESH_HANDLER = CommandHandler("admincache", refresh_admin, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(SET_DESC_HANDLER)
dispatcher.add_handler(SET_STICKER_HANDLER)
dispatcher.add_handler(SETCHATPIC_HANDLER)
dispatcher.add_handler(RMCHATPIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(BUG_HANDLER)
dispatcher.add_handler(PINNED_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(FULLPROMOTE_HANDLER)
dispatcher.add_handler(LOW_PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Admins"
__command_list__ = [
    "setdesc"
    "setsticker"
    "setgpic"
    "delgpic"
    "setgtitle"
    "adminlist",
    "admins", 
    "invitelink", 
    "promote", 
    "fullpromote",
    "lowpromote",
    "demote", 
    "admincache"
]
__handlers__ = [
    SET_DESC_HANDLER,
    SET_STICKER_HANDLER,
    SETCHATPIC_HANDLER,
    RMCHATPIC_HANDLER,
    SETCHAT_TITLE_HANDLER,
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    PINNED_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    FULLPROMOTE_HANDLER,
    LOW_PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]

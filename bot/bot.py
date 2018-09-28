import random

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

from constants import *
from parser.instagram_parser import InstagramParser
from security import *
from util import *

conf = load_file(configuration)
token = conf[token]
channel = conf[channel_name]

bot = telebot.TeleBot(token)
crypto = crypto.Crypto()
buffer = {}
posts = {}


def init_admin(func):
    def wrapper(request):
        cid = request.chat.id

        if not crypto.check_key():
            bot.send_message(cid, hello_msg)
            crypto.encrypt(cid)
            bot.send_message(cid, scan_msg)
        func(request)

    return wrapper


def security(func):
    def wrapper(request):
        cid = request.chat.id
        if crypto.fast_encrypt(cid) == crypto.decipher():
            func(request)
        else:
            bot.send_photo(cid, caption=rooster_msg, photo=open(rooster_jpg, 'rb'))

    return wrapper


def choose_buttons():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(description_text, callback_data=positive_cmd),
               InlineKeyboardButton(negative_text, callback_data=negative_cmd))
    markup.add(InlineKeyboardButton(post_text, callback_data=fast_cmd))
    return markup


def list_buttons(chat_id, flag=True):
    row = []

    markup = InlineKeyboardMarkup()
    size = len(buffer[chat_id])

    if flag:
        if size <= 5:
            add_buttons(markup, row, 1, size)
        else:
            add_buttons(markup, row, 1, 5)
            buttons = [
                InlineKeyboardButton("all", callback_data=all_cmd),
                InlineKeyboardButton(">", callback_data=next_cmd)
            ]
            markup.row(*buttons)
    else:
        add_buttons(markup, row, 5, size)
        buttons = [
            InlineKeyboardButton("all", callback_data=all_cmd),
            InlineKeyboardButton("<", callback_data=prev_cmd)
        ]
        markup.row(*buttons)
    return markup


def add_buttons(markup, row, start, size):
    for item in range(start, size + 1):
        row.append(InlineKeyboardButton(item, callback_data="button_number-" + str(item)))
    markup.row(*row)


def process_comment_step(message):
    post = posts[message.chat.id]
    post.description = message.text
    post_media(post.media, post.description)


def post_media(result, message=None):
    if result.type_content == type_image:
        bot.send_photo(channel, result.src, caption=message)
    elif result.type_content == type_video:
        bot.send_video(channel, result.src, caption=message)


# Commands ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@bot.message_handler(commands=['start'])
@init_admin
@security
def command_start(request):
    pass


@bot.message_handler(regexp=regexp_instagram)
@security
def command_intagram(message):
    chat_id = message.chat.id
    result = InstagramParser().get_content_by_url(message.text)

    if result:
        if isinstance(result, list):
            buffer[chat_id] = result
            bot.reply_to(message, post_question_msg, reply_markup=list_buttons(chat_id))
        else:
            posts[chat_id] = Post(result)
            bot.reply_to(message, description_msg, reply_markup=choose_buttons())
    else:
        bot.send_message(chat_id, "Не могу извлечь контент, это привайный аккаунт!!")


# Commands end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Callback ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@bot.callback_query_handler(func=lambda call: call.data == next_cmd)
def next_post(call):
    if len(buffer[call.from_user.id]) > 1:
        bot.edit_message_text("Post page 2", call.from_user.id, call.message.message_id,
                              reply_markup=list_buttons(call.from_user.id, False))


@bot.callback_query_handler(func=lambda call: call.data == prev_cmd)
def prev_post(call):
    if len(buffer[call.from_user.id]) > 1:
        bot.edit_message_text("Post page 1", call.from_user.id, call.message.message_id,
                              reply_markup=list_buttons(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == all_cmd)
def all_post(call):
    if len(buffer[call.from_user.id]) > 1:
        print("ALL")


@bot.callback_query_handler(func=lambda call: call.data[0:14] == "button_number-")
def choose_number(call):
    if len(buffer[call.from_user.id]) > 1:
        item = buffer[call.from_user.id][int(call.data[14:]) - 1]
        posts[call.from_user.id] = Post(item)

        buffer[call.from_user.id] = {}
        bot.reply_to(call.message.reply_to_message, description_msg, reply_markup=choose_buttons())


@bot.callback_query_handler(func=lambda call: call.data == fast_cmd)
def callback_fast_post(call):
    if posts[call.from_user.id]:
        cid = call.from_user.id

        post = posts[cid]
        post_media(post.media)

        posts[cid] = {}


@bot.callback_query_handler(func=lambda call: call.data == positive_cmd or call.data == negative_cmd)
def callback_content_post_query(call):
    if posts[call.from_user.id]:
        if call.data == positive_cmd:
            replied_message = bot.reply_to(call.message.reply_to_message, "Описание:", reply_markup=ForceReply())
            bot.register_next_step_handler(replied_message, process_comment_step)
        elif call.data == negative_cmd:
            bot.reply_to(call.message.reply_to_message, random.choice(cancel_posts))
            posts[call.from_user.id] = {}


# Callback end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


bot.polling(none_stop=True)

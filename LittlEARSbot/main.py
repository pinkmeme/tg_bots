#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygsheets
import telebot
from telebot import types as tp
import config
import sqlite3
from sqlite3 import Error

token = "tg bot token"
wks = pygsheets.authorize().open('your google table').sheet1


def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path, check_same_thread=False)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection


connection = create_connection("db.sqlite")

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


def set_state(id, state):
    command = "UPDATE users SET state = " + str(state) + " WHERE tgid = " + str(id)
    execute_query(connection, command)


def create_new_user(id):
    command = "INSERT OR IGNORE INTO users (tgid, state) VALUES (" + str(id) + ", 0);"
    execute_query(connection, command)


def request_state(id):
    command = "SELECT state FROM users WHERE tgid = " + str(id)
    return execute_read_query(connection, command)


bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def cmd_start(message):
    create_new_user(message.chat.id)
    set_state(message.chat.id, config.States.start.value)
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("Да!")
    item2 = tp.KeyboardButton("Нет")
    markup.add(item1, item2)

    bot.send_message(message.chat.id,
                     "Привет! Я - бот для опросов LittlEARS. Вы хотите заполнить анкету?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.start.value)
def name_enter(message):
    if message.text == "Да!":
        bot.send_message(message.chat.id, "Отлично!\nУкажите пожалуйста имя ребёнка.")
        set_state(message.chat.id, config.States.name.value)
    elif message.text == "Нет":
        bot.send_message(message.chat.id, "Всего хорошего!")
        set_state(message.chat.id, config.States.end.value)
    else:
        bot.send_message(message.chat.id, "Извините, не разобрался, ответьте пожалуйста 'Да!' или 'Нет'")
        return


@bot.message_handler(content_types=['text'],
                     func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.name.value)
def date_enter(message):
    cur_row_name = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 3)
    wks.update_value(cur_row_name.label, message.text)
    bot.send_message(message.chat.id, "Теперь фамилию ребёнка.")
    set_state(message.chat.id, config.States.surname.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.surname.value)
def date_enter(message):
    cur_row_name = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 4)
    wks.update_value(cur_row_name.label, message.text)
    bot.send_message(message.chat.id, "Дата рождения ребёнка?")
    set_state(message.chat.id, config.States.date.value)


markup = tp.ReplyKeyboardMarkup(resize_keyboard=True)
item1 = tp.KeyboardButton("да")
item2 = tp.KeyboardButton("нет")
markup.add(item1, item2)


@bot.message_handler(content_types=['text'],
                     func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.date.value)
def qu1(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("да")
    item2 = tp.KeyboardButton("нет")
    markup.add(item1, item2)
    cur_row_date = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 2)
    wks.update_value(cur_row_date.label, message.text)
    bot.send_message(message.chat.id, "Пользуется ли ваш ребёнок КИ (кохлеарным имплантом)?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.opt_q1.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q1.value)
def opt_qu1(message):
    if message.text == "да":
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 5)
        wks.update_value(cur_row_q1.label, message.text)
        bot.send_message(message.chat.id, "Введите дату операции по установке импланта")
        set_state(message.chat.id, config.States.opt_q2.value)
    elif message.text == "нет":
        markup1 = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item11 = tp.KeyboardButton("да")
        item21 = tp.KeyboardButton("нет")
        markup1.add(item11, item21)
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 5)
        wks.update_value(cur_row_q1.label, message.text)
        bot.send_message(message.chat.id, "Используете ли вы дополнительные устройства прослушивания?"
                         .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup1)
        set_state(message.chat.id, config.States.opt_q5.value)
    else:
        bot.send_message(message.chat.id, "Извините, не разобрался, ответьте пожалуйста 'да' или 'нет'")
        return


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q2.value)
def opt_qu2(message):
    markup1 = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item11 = tp.KeyboardButton("MED-EL")
    item21 = tp.KeyboardButton("Cochlear")
    item31 = tp.KeyboardButton("Oticon")
    item41 = tp.KeyboardButton("Другое")
    markup1.add(item11, item21, item31, item41)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 6)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Модель какого производителя кохлеарного импланта установлена у ребёнка?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup1)
    set_state(message.chat.id, config.States.opt_q3.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q3.value)
def opt_qu3(message):
    if message.text == "Другое":
        bot.send_message(message.chat.id, "Имплант и процессор какого производителя установлены у вашего ребенка?"
                                          " Напишите название и тип процессора. ")
        set_state(message.chat.id, config.States.opt_q4.value)
    elif message.text == "MED-EL":
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 7)
        wks.update_value(cur_row_q1.label, message.text)
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = tp.KeyboardButton("TEMPO+/OPUS1")
        item2 = tp.KeyboardButton("OPUS2")
        item3 = tp.KeyboardButton("RONDO")
        item4 = tp.KeyboardButton("RONDO 2/3")
        item5 = tp.KeyboardButton("SONNET")
        item6 = tp.KeyboardButton("SONNET 2")
        markup.add(item1, item2, item3, item4, item5, item6)
        bot.send_message(message.chat.id, "Какой слуховой процессор установлен у ребенка? Выберите из предложенных или "
                                          "введите с клавиатуры"
                         .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
        set_state(message.chat.id, config.States.opt_q7.value)
    elif message.text == "Cochlear":
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 7)
        wks.update_value(cur_row_q1.label, message.text)
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = tp.KeyboardButton("Freedom")
        item2 = tp.KeyboardButton("Nucleus6")
        item3 = tp.KeyboardButton("Nucleus7")
        item4 = tp.KeyboardButton("Kanso")
        markup.add(item1, item2, item3, item4)
        bot.send_message(message.chat.id, "Какой слуховой процессор установлен у ребенка? Выберите из предложенных или "
                                          "введите с клавиатуры"
                         .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
        set_state(message.chat.id, config.States.opt_q8.value)
    elif message.text == "Oticon":
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 7)
        wks.update_value(cur_row_q1.label, message.text)
        markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = tp.KeyboardButton("Saphir")
        item2 = tp.KeyboardButton("Neuro1")
        item3 = tp.KeyboardButton("Neuro2")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Какой слуховой процессор установлен у ребенка? Выберите из предложенных или "
                                          "введите с клавиатуры"
                         .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
        set_state(message.chat.id, config.States.opt_q9.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q4.value)
def opt_qu4(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("да")
    item2 = tp.KeyboardButton("нет")
    markup.add(item1, item2)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 11)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Используете ли Вы дополнительные устройства прослушивания?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.opt_q5.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q7.value)
def opt_qu7(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("да")
    item2 = tp.KeyboardButton("нет")
    markup.add(item1, item2)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 8)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Используете ли Вы дополнительные устройства прослушивания?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.opt_q5.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q8.value)
def opt_qu8(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("да")
    item2 = tp.KeyboardButton("нет")
    markup.add(item1, item2)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 9)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Используете ли Вы дополнительные устройства прослушивания?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.opt_q5.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q9.value)
def opt_qu9(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("да")
    item2 = tp.KeyboardButton("нет")
    markup.add(item1, item2)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 10)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Используете ли Вы дополнительные устройства прослушивания?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.opt_q5.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q5.value)
def opt_qu5(message):
    if message.text == "да":
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 12)
        wks.update_value(cur_row_q1.label, message.text)
        bot.send_message(message.chat.id, "Какие дополнительные устройства прослушивания Вы используете? "
                                          "Расскажите подробно.")
        set_state(message.chat.id, config.States.opt_q6.value)
    else:
        cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 12)
        wks.update_value(cur_row_q1.label, message.text)
        bot.send_message(message.chat.id, "Ниже будут 35 вопросов о вашем ребёнке.")
        bot.send_message(message.chat.id, "1. Ваш ребенок реагирует на знакомый голос? "
                                          "Улыбается, смотрит на источник звука, говорит оживленно."
                         .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
        set_state(message.chat.id, 1)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.opt_q6.value)
def opt_qu6(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 13)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Ниже будут 35 вопросов о вашем ребёнке.")
    bot.send_message(message.chat.id, "1. Ваш ребенок реагирует на знакомый голос? "
                                      "Улыбается, смотрит на источник звука, говорит оживленно."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 1)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 1)
def qu1(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 14)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "2. Ваш ребенок слушает, когда кто-то говорит? "
                                      "Слушает, ждет и слушает, смотрит на говорящего более продолжительное время."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 2)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 2)
def qu2(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 15)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "3. Когда кто-то говорит, ваш ребенок поворачивает голову в сторону говорящего?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 3)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 3)
def qu3(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 16)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "4. Ваш ребенок интересуется музыкальными игрушками или игрушками, издающими звуки?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 4)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 4)
def qu4(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 17)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "5. Ваш ребенок ищет взглядом говорящего, если не видит его?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 5)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 5)
def qu5(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 18)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "6. Ваш ребенок слушает радиозаписи или записи с диска либо пленки? "
                                      "Слушает: поворачивается к источнику звука, внимателен, "
                                      "смеется или подпевает/отвечает."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 6)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 6)
def qu6(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 19)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "7. Он реагирует на отдаленные звуки? Когда ребенка зовут из другой комнаты."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 7)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 7)
def qu7(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 20)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "8. Ребенок перестает плакать, когда вы говорите с ним, но он вас не видит? "
                                      "Вы пытаетесь утешить ребенка тихим голосом или песней, без зрительного контакта."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 8)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 8)
def qu8(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 21)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "9. Он отвечает тревогой на раздраженный голос? "
                                      "Ребенок расстроен и начинает плакать."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 9)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 9)
def qu9(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 22)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, '10. Ваш ребенок «узнает» звуки, сопровождающие привычные действия? '
                                      'Музыкальная шкатулка у кровати, колыбельная, шум текущей воды.'
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 10)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 10)
def qu10(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 23)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "11. Ваш ребенок смотрит на источники звука, расположенные слева, справа или позади"
                                      " него? Вы зовете ребенка или что-то говорите, или собака лает, или раздается"
                                      " другой звук — ребенок ищет источник звука и находит его."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 11)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 11)
def qu11(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 24)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "12. Ваш ребенок реагирует на свое имя?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 12)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 12)
def qu12(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 25)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "13. Ваш ребенок смотрит на источники звука, расположенные над или под ним? "
                                      "Тиканье настенных часов или стук падения предмета на пол."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 13)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 13)
def qu13(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 26)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "14. Когда ваш ребенок грустит или не в настроении, можно ли его успокоить или"
                                      " как-то воздействовать на него при помощи музыки?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 14)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 14)
def qu14(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 27)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "15. Слушает ли ваш ребенок телефон? Есть ли ощущение, что он понимает, что"
                                      " кто-то с ним говорит? Когда бабушка или папа звонят ребенку по телефону, ребенок"
                                      " снимает трубку и «слушает»."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 15)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 15)
def qu15(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 28)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "16. Ваш ребенок реагирует на музыку ритмичными движениями? Ребенок двигает"
                                      " ручками/ножками в такт музыке."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 16)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 16)
def qu16(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 29)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "17. Ваш ребенок знает, что определенные звуки связаны с определенными предметами"
                                      " или событиями? Ребенок слышит гул самолета и смотрит на небо или слышит шум"
                                      " мотора и смотрит на дорогу."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 17)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 17)
def qu17(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 30)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "18. Ваш ребенок адекватно реагирует на короткие простые фразы? "
                                      "«Перестань!», «Кака!», «Нельзя!»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 19)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 19)
def qu19(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 31)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "19. Если вы говорите «нет!», ваш ребенок обычно прерывает свою деятельность? "
                                      "Строгое «Нет!» помогает, даже если ребенок не видит вас(!)."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 20)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 20)
def qu20(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 32)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "20. Ваш ребенок знает, как зовут членов семьи? Где...: Папа, Женя, Джурабек, ..."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 21)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 21)
def qu21(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 33)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "21. Ваш ребенок повторяет звуки, если его попросить? «Ааа», «ооо», «иии»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 22)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 22)
def qu22(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 34)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "22. Ребенок выполняет простые инструкции? «Иди ко мне!», «Сними ботиночки!»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 23)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 23)
def qu23(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 35)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "23. Ребенок понимает простые вопросы? «Где животик?»; «Где папа?»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 24)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 24)
def qu24(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 36)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "24. Ваш ребенок приносит предметы, если его попросить? «Принеси мячик!» и т. д."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 25)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 25)
def qu25(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 37)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "25. Ваш ребенок повторяет звуки или слова, которые вы произносите? "
                                      "«Скажи гав-гав», «Скажи б-и-б-и-к-а»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 26)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 26)
def qu26(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 38)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "26. Играя с игрушками, ребенок правильно изображает соответствующие звуки? "
                                      "Машина би-би, корова му-у"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 27)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 27)
def qu27(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 39)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "27. Ребенок знает, что определенные животные произносят определенные звуки? "
                                      "Гав-гав = собака; мяу = кошка; кукареку = петушок"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 28)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 28)
def qu28(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 40)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "28. Ваш ребенок пытается изображать звуки, которые слышит? "
                                      "Звуки животных, бытовых приборов, сирена полицейской машины."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 29)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 29)
def qu29(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 41)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "29. Ваш ребенок правильно повторяет за вами ряд коротких и длинных слогов?"
                                      " «Ла-ла-лаа»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 30)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 30)
def qu30(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 42)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "30. Ваш ребенок правильно выбирает предмет из ряда похожих предметов в ответ на"
                                      " вашу просьбу? Вы играете с игрушечными животными и просите дать вам лошадку, вы"
                                      " играете с цветными мячиками и просите красный мячик."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 31)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 31)
def qu31(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 43)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "31. Ваш ребенок подпевает, когда слышит песни? Потешки"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 32)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 32)
def qu32(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 44)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "32. Ваш ребенок повторяет слова, если его попросить? Скажи бабушке «пока-пока!»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 33)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 33)
def qu33(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 45)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "33. Ваш ребенок любит, когда вы ему читаете? Книга или книга с картинками."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 34)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 34)
def qu34(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 46)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "34. Ребенок выполняет сложные инструкции? «Сними ботиночки и иди ко мне!»"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 35)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 35)
def qu35(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 47)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "35. Ваш ребенок подпевает, когда слышит знакомые песни? Колыбельная"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 36)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 36)
def qu36(message):
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + 0, 48)
    wks.update_value(cur_row_q1.label, message.text)
    bot.send_message(message.chat.id, "Вы медицинский специалист? Это необходимо для введения ID."
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, 37)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == 37)
def qu37(message):
    if message.text == "нет":
        cur_row = pygsheets.Address('B3') + (int(wks.get_value('AZ2')) - 1, 0)
        c = wks.get_value(cur_row.label)
        bot.send_message(message.chat.id, "Спасибо за участие в опросе! Ваш результат - " + c + " баллов.")
        set_state(message.chat.id, config.States.end.value)
    else:
        bot.send_message(message.chat.id, "Укажите ID врача")
        set_state(message.chat.id, config.States.id.value)


@bot.message_handler(func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.id.value)
def ending(message):
    markup = tp.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = tp.KeyboardButton("Да!")
    item2 = tp.KeyboardButton("Нет")
    markup.add(item1, item2)
    cur_row_q1 = pygsheets.Address('A3') + (int(wks.get_value('AZ2')) + -1, 49)
    wks.update_value(cur_row_q1.label, message.text)
    cur_row = pygsheets.Address('B3') + (int(wks.get_value('AZ2')) - 1, 0)
    c = wks.get_value(cur_row.label)
    bot.send_message(message.chat.id, "Спасибо за участие в опросе! Ваш результат - " + c + " баллов.")
    bot.send_message(message.chat.id, "Хотите заполнить опрос заново?"
                     .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    set_state(message.chat.id, config.States.start.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: int(request_state(message.chat.id)[0][0]) == config.States.end.value)
def repeat(message):
    bot.send_message(message.chat.id, "О, это снова вы? Напиши /start, чтобы заполнить опрос заново :)")


bot.infinity_polling()

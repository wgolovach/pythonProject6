import telebot
import sqlite3 as sq
from telebot import types
from datetime import datetime
import time

'''Проверка'''

bot = telebot.TeleBot('5298518813:AAGeUgptj5E52_8myobygU3S-n8dnyvkzig')
my_DB = 'MenuDB.db'
today = datetime.today().date()
today = today.strftime("%d / %m / %Y")


@bot.message_handler(func=lambda message: True)
def home_page(message):

    mess = f'Привіт, {message.from_user.first_name}! \n У цьому боті ти зможеш замовити страви з нашого ресторану!'

    markup = types.InlineKeyboardMarkup()
    start_button = types.InlineKeyboardButton(text=f'🏠 На головну сторінку', callback_data='start')

    markup.add(start_button)

    bot.send_message(message.chat.id, f'{mess}', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    user_id = callback.from_user.id
    order_id = ensure_order_exist(user_id)
    basket_item_count = basket_count(order_id)
    x = 1

    if 'start' in callback.data:
        mess = f'🏠 Головна сторінка'

        markup = types.InlineKeyboardMarkup()
        menu_button = types.InlineKeyboardButton(text=f'🍔 Меню', callback_data='menu')
        old_order_button = types.InlineKeyboardButton(text=f'📝 Мої замовлення', callback_data=f'{x} my_order')
        bascket_button = types.InlineKeyboardButton(text=f'🛒 Корзина ({basket_item_count})', callback_data='basket')

        markup.add(menu_button)
        markup.add(old_order_button)
        markup.add(bascket_button)

        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'{mess}',
                              reply_markup=markup)

    elif 'my_order' in callback.data:
        x = int(callback.data.split()[0])
        old_order(user_id, callback, x)

    elif 'delete_message' in callback.data:
        message_to_delete_ids = callback.data.split()[1].split(',')
        for i in message_to_delete_ids:
            bot.delete_message(callback.message.chat.id, i)

        callback.data = callback.data.split()[2:]
        callback.data = ' '.join(callback.data)

    if callback.data == 'menu':
        with sq.connect(my_DB) as con:
            cur = con.cursor()
            cur.execute("SELECT _rowid_, category FROM category")
            result = cur.fetchall()
        buttons_dict = {i: x for i, x in enumerate(result)}
        keyboard = types.InlineKeyboardMarkup()
        button_list = [types.InlineKeyboardButton(text=x[1], callback_data=f'category {x[0]}') for x in
                       buttons_dict.values()]
        back_button = types.InlineKeyboardButton(text='⬅️ На головну сторінку', callback_data='start')
        for i in button_list:
            keyboard.add(i)
        bascket_button = types.InlineKeyboardButton(text=f'🛒 Корзина ({basket_item_count})', callback_data='basket')
        keyboard.add(bascket_button)
        keyboard.add(back_button)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'🍔 Меню',
                              reply_markup=keyboard)

    elif 'basket' in callback.data:

        basket_list = f'ВАШЕ ЗАМОВЛЕННЯ:\n\n'
        order_sum = 0

        with sq.connect(my_DB) as con:
            cur = con.cursor()
            cur.execute("SELECT item_id, number FROM shopping_cart WHERE order_id = ?", (ensure_order_exist(user_id),))
            item_in_basket = cur.fetchall()
            for i in item_in_basket:
                cur.execute("SELECT item, price FROM menu_item WHERE _rowid_ = ?", (i[0],))
                item_price_in_basket = cur.fetchall()
                basket_list += f'- {item_price_in_basket[0][0]}\n{item_price_in_basket[0][1]} грн. * {i[1]} = {item_price_in_basket[0][1] * i[1]} грн.\n---------------------\n'
                order_sum += item_price_in_basket[0][1] * i[1]

        if order_sum == 0:
            text_empty_basket = f'Зробити замовлення'
            basket_list = f'Ваша корзина порожня'
            callback_data_empty_basket = f'menu'

        else:
            text_empty_basket = f"ОПЛАТИТИ {order_sum} грн."
            callback_data_empty_basket = f'pay {order_sum}'

        keyboard = types.InlineKeyboardMarkup()
        order_sum_button = types.InlineKeyboardButton(text=text_empty_basket, callback_data=callback_data_empty_basket)
        back_button = types.InlineKeyboardButton(text="⬅️ На головну сторінку", callback_data='start')
        keyboard.add(order_sum_button)
        keyboard.add(back_button)

        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'{basket_list}\nДо оплати: {order_sum} грн.',
                              reply_markup=keyboard)

    elif callback.data == 'back_to_home_page':
        home_page(callback.message)
        bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)

    elif 'category' in callback.data:

        category_id = callback.data.split()[1]

        with sq.connect(my_DB) as con:
            cur = con.cursor()
            cur.execute("SELECT item, price, _rowid_ FROM menu_item WHERE category = ?", (category_id,))
            result = cur.fetchall()
            cur.execute("SELECT category FROM category WHERE _rowid_ = ?", (category_id,))
            category_name = cur.fetchone()[0]

        print(f'-------------\nCategory\ncategory_id = {category_id}\ncategory_name = {category_name}\n-----------')

        buttons_dict = {i: x for i, x in enumerate(result)}
        keyboard = types.InlineKeyboardMarkup()
        back_button = types.InlineKeyboardButton(text="⬅️ Назад", callback_data='menu')
        button_list = [types.InlineKeyboardButton(text=f'🔘 {x[0]} - {x[1]} грн.',
                                                  callback_data=f'delete_message {callback.message.id} menu_item {x[2]}')
                       for x in
                       buttons_dict.values()]
        for i in button_list:
            keyboard.add(i)
        bascket_button = types.InlineKeyboardButton(text=f'🛒 Корзина ({basket_item_count})', callback_data='basket')
        keyboard.add(bascket_button)

        keyboard.add(back_button)

        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'{category_name}',
                              reply_markup=keyboard)

    elif 'menu_item' in callback.data:

        item_id = callback.data.split()[1]

        show_menu_item(callback, item_id, order_id)

    elif 'pay' in callback.data:

        order_sum = 0

        with sq.connect(my_DB) as con:
            cur = con.cursor()
            cur.execute("SELECT item_id, number FROM shopping_cart WHERE order_id = ?", (ensure_order_exist(user_id),))
            item_in_basket = cur.fetchall()
            for i in item_in_basket:
                cur.execute("SELECT item, price FROM menu_item WHERE _rowid_ = ?", (i[0],))
                item_price_in_basket = cur.fetchall()
                order_sum += item_price_in_basket[0][1] * i[1]

            cur.execute("UPDATE user_order SET order_price = ? WHERE user_id = ? AND  order_status = 0",
                        (order_sum, user_id))
            cur.execute("UPDATE user_order SET order_status = 1 WHERE user_id = ? AND  order_status = 0", (user_id,))

            basket_list = f'Замовлення №{order_id}\nна сумму {order_sum} грн.\nсплачено!'

            keyboard = types.InlineKeyboardMarkup()
            back_button = types.InlineKeyboardButton(text="⬅️ На головну сторінку", callback_data='start')
            keyboard.add(back_button)

            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=basket_list,
                                  reply_markup=keyboard)

            print('pay')

    elif 'order_edit' in callback.data:
        item_id = callback.data.split()[1]
        operation = callback.data.split()[2]
        previous_message_id = int(callback.data.split()[3])

        with sq.connect(my_DB) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT number FROM shopping_cart WHERE item_id = ? AND order_id =?", (item_id, order_id))
            order_item_count = cur.fetchone()

            if order_item_count is None:
                order_item_count = [0]
                cur.execute("INSERT INTO shopping_cart (item_id, number, order_id) VALUES (?, ?, ?)",
                            (item_id, 0, order_id))

            order_item_count = int(order_item_count[0])

            if operation == '+':
                order_item_count += 1
                mess_text = f'Товар додано в кошик'
            else:
                order_item_count -= 1
                mess_text = f'Товар видалено з кошика'

            if order_item_count > 0:
                cur.execute("UPDATE shopping_cart SET number = ? WHERE item_id = ? AND order_id = ?", (
                    order_item_count, item_id, order_id))
                print('update')
            else:
                cur.execute(
                    "DELETE FROM shopping_cart WHERE item_id = ? AND order_id = ?", (item_id, order_id))

        show_menu_item(callback, item_id, order_id, previous_message_id)
        msg = bot.send_message(callback.message.chat.id, mess_text)
        time.sleep(0.5)
        bot.delete_message(callback.message.chat.id, msg.message_id)


def ensure_order_exist(user_id):
    with sq.connect(my_DB) as con:
        cur = con.cursor()
        cur.execute(
            "SELECT _rowid_ FROM user_order WHERE user_id = ? AND order_status = 0", (user_id,))
        open_order = cur.fetchone()
        if open_order is None:
            cur.execute(
                "INSERT INTO user_order (user_id, order_date, order_price, order_status) VALUES (?, ?, ?, ?)",
                (user_id, today, 0, 0))
            return cur.lastrowid
        else:
            return open_order[0]


def show_menu_item(callback, item_id, order_id, previous_buttons_message_id=None):
    print(f'your_callback = {item_id}')

    with sq.connect(my_DB) as con:
        cur = con.cursor()
        cur.execute("SELECT item, category, price, photo FROM menu_item WHERE _rowid_ = ?", (item_id,))
        menu_item = cur.fetchone()
        order_item_count = cur.execute(
            "SELECT number FROM shopping_cart WHERE item_id = ? AND order_id =?", (item_id, order_id)).fetchone()

        if order_item_count is None:
            order_item_count = [0]

        if (previous_buttons_message_id is None) or (previous_buttons_message_id == ""):
            photo_message = bot.send_photo(callback.message.chat.id, menu_item[3])
            photo_message_id = photo_message.message_id
            buttons_message_id = photo_message_id + 1
        else:
            photo_message_id = previous_buttons_message_id - 1
            buttons_message_id = previous_buttons_message_id

        keyboard = types.InlineKeyboardMarkup()
        back_button = types.InlineKeyboardButton(text="⬅️ Назад",
                                                 callback_data=f'delete_message {photo_message_id} category {menu_item[1]}')
        back_to_main = types.InlineKeyboardButton(text="🍔 Назад до головного меню",
                                                  callback_data=f'delete_message {photo_message_id} menu')
        minus_button = types.InlineKeyboardButton(text="➖",
                                                  callback_data=f'order_edit {item_id} - {buttons_message_id}')
        plus_button = types.InlineKeyboardButton(text="➕", callback_data=f'order_edit {item_id} + {buttons_message_id}')
        cart_button = types.InlineKeyboardButton(text=f' 🛒 {order_item_count[0]}', callback_data=f'bascket')
        keyboard.add(minus_button, cart_button, plus_button)
        keyboard.add(back_button)
        keyboard.add(back_to_main)

        if not ((previous_buttons_message_id is None) or (previous_buttons_message_id == "")):
            bot.edit_message_text(chat_id=callback.message.chat.id, text=f'{menu_item[0]} - {menu_item[2]} грн',
                                  message_id=previous_buttons_message_id, reply_markup=keyboard)
        else:
            bot.send_message(callback.message.chat.id, f'{menu_item[0]} - {menu_item[2]} грн', reply_markup=keyboard)


def basket_count(order_id):
    with sq.connect(my_DB) as con:
        cur = con.cursor()

        cur.execute("SELECT number FROM shopping_cart WHERE order_id = ?", (order_id,))
        number_item_in_basket = cur.fetchall()
        item_in_basket_count = 0
        for i in number_item_in_basket:
            item_in_basket_count += i[0]
        print(f'number_item_in_basket = {item_in_basket_count}')
        return item_in_basket_count


def old_order(user_id, callback, x):

    basket_list = f'ВАШЕ ЗАМОВЛЕННЯ:\n\n'
    order_sum = 0

    with sq.connect(my_DB) as con:
        cur = con.cursor()
        cur.execute("SELECT _rowid_, order_date, order_price FROM user_order WHERE order_status = 1 AND user_id = ? AND order_price > 0", (user_id,))
        old_user_order = list(cur.fetchall())

        if len(old_user_order) > 0:

            if x < 1:
                x = len(old_user_order)
            elif x > len(old_user_order):
                x = 1

            now_show_order = old_user_order[len(old_user_order) - x]

            cur.execute("SELECT item_id, number FROM shopping_cart WHERE order_id = ?", (now_show_order[0],))
            this_order_id = now_show_order[0]
            this_order_date = now_show_order[1]
            this_order_sum = now_show_order[2]
            print(f'this_order_id = {this_order_id}')
            print(f'this_order_date = {this_order_date}')
            print(f'this_order_sum = {this_order_sum}')
            item_in_basket = cur.fetchall()

            for i in item_in_basket:
                this_order_item_id = i[0]
                this_order_item_number = i[1]
                print(f'this_order_item_id = {this_order_item_id} - this_order_item_number = {this_order_item_number}')

                cur.execute("SELECT item, price FROM menu_item WHERE _rowid_ = ?", (this_order_item_id,))
                item_price_in_basket = cur.fetchall()[0]
                this_order_item_name = item_price_in_basket[0]
                this_order_item_price = item_price_in_basket[1]
                print(f'this_order_item_name = {this_order_item_name}')
                print(f'this_order_item_price = {this_order_item_price}')

                basket_list += f'- {this_order_item_name}\n{this_order_item_price} грн. * {this_order_item_number} = {this_order_item_price * this_order_item_number} грн.\n---------------------\n'
                order_sum += this_order_item_price * this_order_item_number
            print('---------------')

            keyboard = types.InlineKeyboardMarkup()
            previous_order_button = types.InlineKeyboardButton(text=f'⬅️', callback_data=f'{x - 1} my_order')
            next_order_button = types.InlineKeyboardButton(text=f'➡️', callback_data=f'{x + 1} my_order')
            number_of_order_button = types.InlineKeyboardButton(text=f'{x} з {len(old_user_order)}', callback_data='1')
            back_button = types.InlineKeyboardButton(text="⬅️ На головну сторінку", callback_data='start')
            keyboard.add(previous_order_button, number_of_order_button, next_order_button)
            keyboard.add(back_button)

            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'{this_order_date}\n\n{basket_list}\nСплачено {order_sum} грн.\n', reply_markup=keyboard)
        else:

            keyboard = types.InlineKeyboardMarkup()
            back_button = types.InlineKeyboardButton(text="⬅️ На головну сторінку", callback_data='start')
            keyboard.add(back_button)

            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                  text=f'Ви ще не зробили жодного замовлення',
                                  reply_markup=keyboard)


bot.infinity_polling()

import configparser
import telebot
from telethon.sessions import sqlite
from telethon.sync import TelegramClient
import asyncio
import sqlite3
from telethon.tl.types import Config
import os



config = configparser.ConfigParser()


def insert_data(parts, crsr, sqlconn, titleg):
    for p in parts:
        crsr.execute("INSERT INTO {} VALUES (?, ?, ?, ?);".format(
            titleg), (p.id, p.username, p.first_name, p.last_name))
        sqlconn.commit()


async def search_insert_data(link_list):
    config.read("config.ini")
    api_id = config["Telegram"]["api_id"]
    api_hash = config["Telegram"]["api_hash"]
    username = config["Telegram"]["username"]

    client = TelegramClient(username, api_id, api_hash)
    client = await client.start()

    sqlite_connection = sqlite3.connect("users.db")
    cursor = sqlite_connection.cursor()


    for link in link_list:
        if link == "": continue

        group = await client.get_entity(link)
        participants = await client.get_participants(link)
        print(participants)
        titleg = group.title
        titleg = titleg.replace(' ', '_')

        try:
            insert_data(participants, cursor, sqlite_connection, titleg)
        except:
            print("dont exists")
            sqlite_create_table_query = """CREATE TABLE {} (
                                            id INTEGER,
                                            username text,
                                            first_name text,
                                            last_name text);""".format(titleg)

            cursor.execute(sqlite_create_table_query)
            sqlite_connection.commit()
            insert_data(participants, cursor, sqlite_connection, titleg)

    cursor.close()
    sqlite_connection.close()




bot = telebot.TeleBot(config["Bot"]["token"])

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "groups?")


@bot.message_handler(content_types=["text"])
def one_group_handler(message):
    data = search_insert_data([message.text])

    with open("users.db", "rb") as data:
        bot.send_document(message.chat.id, data)


@bot.message_handler(content_types=['document'])
def start_message(message): 
    file_info = bot.get_file(message.document.file_id)
    downloaded_list = bot.download_file(file_info.file_path)

    file_info = bot.get_file(message.document.file_id)
    link_list = bot.download_file(file_info.file_path)
    link_list = downloaded_list.decode().split("\r\n")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(search_insert_data(link_list))


    with open("users.db", "rb") as data:
        bot.send_document(message.chat.id, data)


    os.remove("db/users.db")
    
 

bot.infinity_poling()


import requests
import configparser
import mysql.connector
from datetime import datetime
from time import sleep

## For the time beeing
user_names = []
user_list = []
broadcast = False

###########
# Configs #
###########

# Get database config
config = configparser.RawConfigParser()
config.read("./database.ini")
dbhost = config.get("Database", "dbhost")
database = config.get("Database", "database")
dbuser = config.get("Database", "dbuser")
dbpass = config.get("Database", "dbpass")

# Get the Database running
db = mysql.connector.connect(host=dbhost,
                             database=database,
                             user=dbuser,
                             password=dbpass)
cursor = db.cursor()

# Telegram token
sqlquery = "SELECT config_value FROM configs WHERE config_name = 'telegram_token'"
cursor.execute(sqlquery)
records = cursor.fetchone()
tgbot_token = records[0]

# Broadcast channel

sqlquery = "SELECT config_value FROM configs WHERE config_name = 'broadcast_channel'"
cursor.execute(sqlquery)
records = cursor.fetchone()
broadcast_channel = records[0]

##############
# user class #
##############

class User:
    def __init__(self, name, rating_solo, rating_team, last_update, rank_solo, rank_team):
        self.name = name
        self.rating_solo = rating_solo
        self.rating_team = rating_team
        self.last_update = last_update
        self.rank_solo = rank_solo
        self.rank_team = rank_team



###################
# ao2.net methods #
###################

# Get leaderboard from bot
def get_leaderboard(leaderboard_id, start, count):
    try:
        api_url = "https://aoe2.net/api/leaderboard?game=aoe2de&leaderboard_id={}&start={}&count={}".format(leaderboard_id, start, count)
        print(api_url)
        api_response = requests.get(api_url)
        return api_response.json()
    except:
        return False

####################
# Telegram methods #
####################

# Get updates from bot
def get_messages(offset_func):
    try:
        offset_url = "https://api.telegram.org/bot" + str(tgbot_token) + "/getUpdates?offset=" + offset_func
        bot_messages = requests.get(offset_url)
        return bot_messages.json()
    except:
        print("Error: Telegram API failed!")
        return False

# Send message to a chat
def send_message(chat, message_func):
    try:
        requests.get("https://api.telegram.org/bot" + str(tgbot_token) + "/sendMessage?chat_id=" + str(chat) + "&text=" + str(message_func))
        return True
    except:
        print("Error: Could not set message!")
        return False


#######
# Bot #
#######

# Get enabled users from database
sqlquery = "select * from users"
cursor.execute(sqlquery)
records = cursor.fetchall()

for player in records:
    user_object = User(player[1], player[2], player[3], player[4], player[6], player[7])
    user_list.append(user_object)


for user in user_list:
    user_names.append(user.name)

while True:
    broadcast = False
    start = 5000
    end = 11000
    requests_needed = int((end-start)/1000)

    for request in range(requests_needed):
        players = get_leaderboard(3, start, 1000)
        for player in players["leaderboard"]:
            for user in user_list:
                if user.name == player["name"]:
                    if user.rating_solo != player["rating"]:
                        user.rating_solo = player["rating"]
                        sqlquery = "UPDATE users SET rating_solo = '{}' WHERE name = '{}'".format(user.rating_solo, user.name)
                        cursor.execute(sqlquery)
                        broadcast = True

                    user.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sqlquery = "UPDATE users SET last_update = '{}' WHERE name = '{}'".format(user.last_update, user.name)
                    cursor.execute(sqlquery)

                    user.steam_id = player["steam_id"]
                    sqlquery = "UPDATE users SET steam_id = '{}' WHERE name = '{}'".format(user.steam_id, user.name)
                    cursor.execute(sqlquery)

                    user.rank_solo = player["rank"]
                    sqlquery = "UPDATE users SET rank_solo = '{}' WHERE name = '{}'".format(user.rank_solo, user.name)
                    cursor.execute(sqlquery)

                    db.commit()

                    print("Set User: {} solo rating to {} - Update time: {}".format(user.name, user.rating_solo, user.last_update))

        start += 1000

    start = 15000
    end = 19000
    requests_needed = int((end-start)/1000)

    for request in range(requests_needed):
        players = get_leaderboard(4, start, 1000)
        for player in players["leaderboard"]:
            for user in user_list:
                if user.name == player["name"]:
                    if user.rating_team != player["rating"]:
                        user.rating_team = player["rating"]
                        sqlquery = "UPDATE users SET rating_team = '{}' WHERE name = '{}'".format(user.rating_team, user.name)
                        cursor.execute(sqlquery)
                        broadcast = True

                    user.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sqlquery = "UPDATE users SET last_update = '{}' WHERE name = '{}'".format(user.last_update, user.name)
                    cursor.execute(sqlquery)

                    user.steam_id = player["steam_id"]
                    sqlquery = "UPDATE users SET steam_id = '{}' WHERE name = '{}'".format(user.steam_id, user.name)
                    cursor.execute(sqlquery)

                    user.rank_team = player["rank"]
                    sqlquery = "UPDATE users SET rank_team = '{}' WHERE name = '{}'".format(user.rank_team, user.name)
                    cursor.execute(sqlquery)

                    db.commit()

                    print("Set User: {} solo rating to {} - Update time: {}".format(user.name, user.rating_team, user.last_update))

        start += 1000

    if broadcast:
        # Solo 1v1
        user_list_with_rating = []
        for user in user_list:
            if user.rating_solo:
                user_list_with_rating.append(user)
        user_list_sorted = sorted(user_list_with_rating, key=lambda x: x.rating_solo, reverse=True)

        leaderboard_solo = "1v1 Leaderboard:\n----------------------\n"
        for user in user_list_sorted:
            if user.rating_solo:
                leaderboard_solo = leaderboard_solo + "Rank: {} Rating: {} {}\n".format(user.rank_solo, user.rating_solo, user.name)

        # Team
        user_list_with_rating = []
        for user in user_list:
            if user.rating_team:
                user_list_with_rating.append(user)
        user_list_sorted = sorted(user_list_with_rating, key=lambda x: x.rating_team, reverse=True)

        leaderboard_team = "Team Leaderboard:\n------------------------\n"
        for user in user_list_sorted:
            if user.rating_team:
                leaderboard_team = leaderboard_team + "Rank: {} Rating: {} {}\n".format(user.rank_team, user.rating_team, user.name)

        one_msg = leaderboard_solo + "\n" + leaderboard_team
        send_message(broadcast_channel, one_msg)

    sleep(600)


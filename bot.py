import telebot
import requests
from googletrans import Translator
import json
import os
import difflib
import random
import re

bot = telebot.TeleBot("496518333:AAEnk2vAp8YvbZLcR86p-dZTD3-K-Wganhw")
dir_path = r"D:\Programming\PycharmProjects\taxi-telegram-bot"
path_count = "count.json"
path_exclude = "exclude.json"
path_cuisine = "cuisines.json"
path_mealtype = "mealtype.json"

translator = Translator()

count_db = {}
exclude_db = {}
cuisine_db = {}
mealtype_db = {}
mealtypes = ['All', 'Breads', 'Breakfast', 'Cakes', 'Casseroles', 'Cookies', 'Desserts', 'Dinner', 'Dips', 'Drinks', 'Fish recipes', 'Grilling & BBQ', 'Kid Friendly', 'Meat recipes', 'Poutry recipes', 'Quick & Easy', 'Salad Dressings', 'Salads', 'Sandwiches', 'Sauses', 'Seafood recipies', 'Slow Cooker', 'Soups', 'Veggie recipes']
cuisines = ['All', 'Asian', 'Caribbean', 'Chinese', 'French', 'German', 'Indian & Thai', 'Italian', 'Mediterranean', 'Mexican', 'Tex-Mex & Southwest']

results_db = {}
suggestions_db = {}

def read_data(path):
    data = json.load(open(path))
    data = {int(k): v for k, v in data.items()}
    return data


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

if os.path.exists(os.path.join(dir_path, path_count)):
    count_db = read_data(path_count)
else:
    count_db = {}

if os.path.exists(os.path.join(dir_path, path_exclude)):
    exclude_db = read_data(path_exclude)
else:
    exclude_db = {}

if os.path.exists(os.path.join(dir_path, path_cuisine)):
    cuisine_db = read_data(path_exclude)
else:
    cuisine_db = {}

if os.path.exists(os.path.join(dir_path, path_mealtype)):
    mealtype_db = read_data(path_mealtype)
else:
    mealtype_db = {}

@bot.message_handler(commands=['start'])
def start(message):
    print(message.chat.id)
    bot.send_message(message.chat.id, 'Start creating recipes with /cook <ingridients>')

@bot.message_handler(commands=['cook'])
def check(message):
    print(message.chat.id)
    ingridients = message.text[6:]
    ingridients = re.sub(r'\W+,', '', ingridients)
    ingridients = translator.translate(ingridients, dest='en').text
    ingridients = "".join(ingridients.split())
    if not message.chat.id in count_db:
        count_db[message.chat.id] = 5
        with open('count.json', 'w') as outfile:
            json.dump(count_db, outfile)
    if not message.chat.id in exclude_db:
        exclude_db[message.chat.id] = ""
        with open('exclude.json', 'w') as outfile:
            json.dump(exclude_db, outfile)
    catname = ""
    if message.chat.id in cuisine_db:
        catname = cuisine_db[message.chat.id]
    if message.chat.id in mealtype_db:
        if len(catname) > 0:
            catname = catname + ',' + mealtype_db[message.chat.id]
        else:
            catname = mealtype_db[message.chat.id]

    r = requests.post('http://www.supercook.com/dyn/results',
                      data={"needsimage": 1, "catname": catname, "kitchen": ingridients, "start": 0,
                            "exclude": exclude_db[message.chat.id]})
    text_dict = dict(json.loads(r.text))
    results = text_dict['results']
    random.shuffle(results)
    total_can_make_right_now = text_dict["total_can_make_right_now"]
    if total_can_make_right_now > 40:
        total_can_make_right_now = 40
    if total_can_make_right_now == 0:
        suggestions_db[message.chat.id] = []
        temp = results[total_can_make_right_now:]
        for i in temp:
            if len(i['uses']) > 0:
                suggestions_db[message.chat.id].append(i)
    results = results[:total_can_make_right_now]
    random.shuffle(results)
    results_db[message.chat.id] = results[:]

    bot.send_message(message.chat.id, 'Total recipes found: ' + str(total_can_make_right_now))
    if total_can_make_right_now < int(count_db[message.chat.id]):
        count = total_can_make_right_now
    else:
        count = int(count_db[message.chat.id])

    if total_can_make_right_now > 0:
        for i in range(count):
            bot.send_message(message.chat.id, results[i]['title'] + "\n" + results[i]['url'])
            results_db[message.chat.id].pop(0)
        if len(results_db[message.chat.id]) > 0:
            if len(results_db[message.chat.id]) < int(count_db[message.chat.id]):
                bot.send_message(message.chat.id,
                                 'Show next ' + str(len(results_db[message.chat.id])) + ' results with /next')
            else:
                bot.send_message(message.chat.id, 'Show next ' + str(count_db[message.chat.id]) + ' results with /next')
    else:
        bot.send_message(message.chat.id, "Can't find any recepies with that.")
        if len(suggestions_db[message.chat.id]) > 0:
            bot.send_message(message.chat.id, "We can show you up to 5 suggestions.\n Use /suggest")

@bot.message_handler(commands=['suggest'])
def showsuggestions(message):
    if message.chat.id in suggestions_db:
        if len(suggestions_db[message.chat.id])>0:
            count = 5
            if len(suggestions_db[message.chat.id])<count:
                count = len(suggestions_db[message.chat.id])
            for i in range(count):
                bot.send_message(message.chat.id, suggestions_db[message.chat.id][i]['title'] + "\nYou need: " + ', '.join(suggestions_db[message.chat.id][i]['needs']) + '\n' + suggestions_db[message.chat.id][i]['url'])
            for i in range(count):
                suggestions_db[message.chat.id].pop(0)
        else:
            bot.send_message(message.chat.id, 'No suggestions to show')
            del results_db[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'You don`t have suggestions to show')


@bot.message_handler(commands=['exclude'])
def exclude(message):
    print(message.chat.id)
    excluding = message.text[9:]
    excluding = translator.translate(excluding, dest='en').text
    excluding = "".join(excluding.split())
    excluding = excluding.replace('vegan', 'poultry,meat,dairy,shellfish,fish,eggs,honey')
    excluding = excluding.replace('vegetarian', 'poultry,meat,fish,shellfish')
    excluding = excluding.replace('pestacatarian', 'poultry,meat')
    if len(excluding) > 0 and excluding != "clear":
        exclude_db[message.chat.id] = excluding
        bot.send_message(message.chat.id, 'Excludings updated')
        with open('exclude.json', 'w') as outfile:
            json.dump(exclude_db, outfile)
    elif len(excluding) == 0 or excluding == "clear":
        exclude_db[message.chat.id] = ""
        with open('exclude.json', 'w') as outfile:
            json.dump(exclude_db, outfile)
        bot.send_message(message.chat.id, 'Excludings cleared')
    else:
        bot.send_message(message.chat.id, 'Wrong arguments')
        with open('exclude.json', 'w') as outfile:
            json.dump(exclude_db, outfile)


@bot.message_handler(commands=['count'])
def count(message):
    print(message.chat.id)
    counting = message.text[7:]
    if RepresentsInt(counting):
        count_db[message.chat.id] = counting
        bot.send_message(message.chat.id, 'Count updated')
    else:
        bot.send_message(message.chat.id, 'Not a number')
    with open('count.json', 'w') as outfile:
        json.dump(count_db, outfile)


@bot.message_handler(commands=['help'])
def command_help(message):
    print(message.chat.id)
    bot.send_message(chat_id=message.chat.id, text="List of commands:")
    bot.send_message(chat_id=message.chat.id, text= "/cook < ingridients > - find suitable recipes")
    bot.send_message(chat_id= message.chat.id,text = "/next - show next n results")
    bot.send_message(chat_id=message.chat.id, text= "/exclude < ingridients > - exclude some ingridiens or included types(vegan, vegetarian, pestacatarian)")
    bot.send_message(chat_id=message.chat.id, text="/count < number > - amount of recipes in response")
    bot.send_message(chat_id=message.chat.id, text="/cuisine < cuisine > - set cuisine type cuisines - list all cuisine types")
    bot.send_message(chat_id=message.chat.id, text="/mealtype < type > - set meal type mealtypes - list all meal types")
    bot.send_message(chat_id=message.chat.id, text="/listsettings - list your settings separate ingridients by ',' you can type  ingridients in any languages")


@bot.message_handler(commands=['cuisine'])
def cuisine(message):
    print(message.chat.id)
    cuisine_type = message.text[9:]
    cuisine_type = translator.translate(cuisine_type, dest='en').text
    cuisine_type = "".join(cuisine_type.split()).title()
    if cuisine_type in cuisines:
        if cuisine_type == 'All':
            cuisine_type = ""
        cuisine_db[message.chat.id] = cuisine_type
        with open('cuisines.json', 'w') as outfile:
            json.dump(cuisine_db, outfile)
        bot.send_message(message.chat.id, 'Cuisine changed')
    else:
        probable_type = difflib.get_close_matches(cuisine_type, cuisines, 1, 0.4)
        if len(probable_type) > 0:
            bot.send_message(message.chat.id, 'Maybe you meant "' + probable_type[0] + '"? Applying it.')
            cuisine_db[message.chat.id] = probable_type[0]
            with open('cuisines.json', 'w') as outfile:
                json.dump(cuisine_db, outfile)
        else:
            bot.send_message(message.chat.id, 'Can not find this cuisine. Use /cuisines to list all available')


@bot.message_handler(commands=['mealtype'])
def mealtype(message):
    print(message.chat.id)
    meal_type = message.text[10:]
    meal_type = translator.translate(meal_type, dest='en').text
    meal_type = "".join(meal_type.split()).title()
    if meal_type in mealtypes:
        if meal_type == 'All':
            meal_type = ""
        mealtype_db[message.chat.id] = meal_type
        with open('mealtype.json', 'w') as outfile:
            json.dump(mealtype_db, outfile)
        bot.send_message(message.chat.id, 'Meal type changed')
    else:
        probable_type = difflib.get_close_matches(meal_type, mealtypes, 1, 0.4)
        if len(probable_type) > 0:
            bot.send_message(message.chat.id, 'Maybe you meant "' + probable_type[0] + '"? Applying it.')
            mealtype_db[message.chat.id] = probable_type[0]
            with open('mealtype.json', 'w') as outfile:
                json.dump(mealtype_db, outfile)
        else:
            bot.send_message(message.chat.id, 'Can nott find this meal type. Use /mealtypes to list all available')


@bot.message_handler(commands=['mealtypes'])
def mealtypes_list(message):
    print(message.chat.id)
    bot.send_message(message.chat.id, ', '.join(mealtypes))


@bot.message_handler(commands=['cuisines'])
def cuisines_list(message):
    print(message.chat.id)
    bot.send_message(message.chat.id, ', '.join(cuisines))


@bot.message_handler(commands=['listsettings'])
def settings_list(message):
    print(message.chat.id)
    settingslist = "Your settings:\n"
    if message.chat.id in count_db:
        settingslist += '    Count: ' + str(count_db[message.chat.id]) + '\n'
    else:
        settingslist += '    Count: 5\n'
    if message.chat.id in exclude_db:
        exclude_value = "none"
        if exclude_db[message.chat.id] != "":
            exclude_value = exclude_db[message.chat.id]
        settingslist += '    Excluded ingridients: ' + exclude_value + '\n'
    else:
        settingslist += '    Excluded ingridients: none\n'
    if message.chat.id in cuisine_db:
        cuisine_value = "all"
        if cuisine_db[message.chat.id] != "":
            cuisine_value = cuisine_db[message.chat.id]
        settingslist += '    Cuisine: ' + cuisine_value + '\n'
    else:
        settingslist += '    Cuisine: all\n'
    if message.chat.id in mealtype_db:
        mealtype_value = "all"
        if mealtype_db[message.chat.id] != "":
            mealtype_value = mealtype_db[message.chat.id]
        settingslist += '    Meal type: ' + mealtype_value + '\n'
    else:
        settingslist += '    Meal type: all\n'

    bot.send_message(message.chat.id, settingslist)


@bot.message_handler(commands=['next'])
def shownext(message):
    print(message.chat.id)
    if message.chat.id in results_db:
        if len(results_db[message.chat.id])>0:
            if len(results_db[message.chat.id]) < int(count_db[message.chat.id]):
                count = len(results_db[message.chat.id])
            else:
                count = int(count_db[message.chat.id])
            for i in range(count):
                bot.send_message(message.chat.id, results_db[message.chat.id][i]['title'] + "\n" + results_db[message.chat.id][i]['url'])
            results_db[message.chat.id] = results_db[message.chat.id][count:]
            if len(results_db[message.chat.id])>0:
                if len(results_db[message.chat.id]) < int(count_db[message.chat.id]):
                   bot.send_message(message.chat.id, 'Show next ' + str(len(results_db[message.chat.id])) + ' results with /next')
                else:
                    bot.send_message(message.chat.id, 'Show next '+str(count_db[message.chat.id]) + ' results with /next')
        else:
            bot.send_message(message.chat.id, 'No recipes to show')
            del results_db[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'You don`t have recipes to show')

bot.polling()





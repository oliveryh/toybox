#!/usr/bin/env python
# coding: utf-8

# - List checklist by categories
# - Save to notion checklist instead of printing in chat

from telegram import Bot

TOKEN="SECRET"

questions = [
    ('weather_sun', 'Will it be sunny?'),
    ('weather_cold', 'Will it be cold?'),
    ('weather_rain', 'Will it be raining?'),
    ('transport_driving', 'Will you be driving?'),
    ('transport_flight', 'Are you taking a flight?'),
    ('transport_train', 'Are you taking a train?'),
    ('transport_tube', 'Are you taking the tube?'),
    ('visiting_home', 'Are you visiting home?'),
    ('leaving_country', 'Are you leaving the country?'),
    ('overnight', 'Are you staying for multiple days?'),
    ('sports', 'Are you going to do any sports?'),
    ('formal', 'Will you be going for a nice meal?'),
]

checklist = {
    'accessories': [
        ('sunglasses', ['weather_sun']),
        ('umbrella', ['weather_rain']),
        ('water bottle', ['default']),
        ('watch', ['default']),
    ],
    'toiletries': [
        ('suncream', ['weather_sun']),
        ('tooth brush', ['overnight']),
        ('tooth paste', ['overnight']),
    ],
    'clothing': [
        ('waterproof jacket', ['weather_rain']),
        ('jumper', ['weather_cold']),
        ('underwear', ['overnight']),
        ('socks', ['overnight']),
        ('t-shirt', ['formal']),
        ('trousers', ['formal']),
        ('leather shoes', ['formal']),
        ('sports t-shirt', ['sports']),
        ('sports shorts', ['sports']),
        ('trainers', ['sports']),
    ],
    'documents': [
        ('driving license', ['transport_driving']),
        ('passport', ['transport_flight', 'leaving_country']),
    ],
    'technology': [
        ('phone', ['default']),
        ('phone charger', ['overnight']),
        ('gps holder', ['transport_driving']),
        ('earphones', ['transport_flight', 'transport_train']),
        ('adaptors', ['leaving_country']),
        ('ear plugs', ['transport_tube']),
    ],
    'digital': [
        ('flight reservation', ['transport_flight']),
        ('check-in', ['transport_flight']),
    ],
    'tasks': [
        ('travel insurance details', ['leaving_country']),
        ('car insurance details', ['transport_driving']),
    ],
    'every day carry': [
        ('parents house keys', ['visiting_home']),
        ('keys', ['default']),
        ('wallet', ['default']),
        ('face mask', ['default']),
    ],
}

def telegram_escape(string):
    return string.replace("-", "\-")

def validate_tags():
    valid_tags = [question[0] for question in questions] + ['default']
    for category, items in checklist.items():
        for item, tags in items:
            for tag in tags:
                if tag not in valid_tags:
                    print(f"Can't find {tag} in tags")
                    return False
    return True

validate_tags()

def add_tag_to_bag(tag):
    for category, items in checklist.items():
        for item, tags in items:
            if tag in tags:
                bag.add((item, category))

#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from telegram.constants import PARSEMODE_MARKDOWN_V2

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENDER, PHOTO, LOCATION, BIO = range(4)
NEXT_QUESTION = 0
ANSWER = 1
current_question = 0

def question(update: Update, context: CallbackContext) -> int:
    """Stores the info about the user and ends the conversation."""
    reply_keyboard = [['Yes', 'No']]
    
    print("Q")
    
    global current_question
    global bag
    global questions
    
    num_questions = len(questions)
    response = update.message.text
    
    print("Response: " + response)
    
    if response == '/start':
        current_question = 0
        bag = set()
        add_tag_to_bag('default')
    else:
        
        if response == 'Yes':
            tag, question_string = questions[current_question]
            add_tag_to_bag(tag)
                
        current_question += 1

    if current_question < num_questions:
        tag, question_string = questions[current_question]
        update.message.reply_text(
            question_string,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'
            ),
        )
        return NEXT_QUESTION
    else:
        print("Bag: " + str(bag))
            
        from collections import defaultdict
        res = defaultdict(list)
        for v, k in bag: res[k].append(v)

        response_text = []

        for k in res.keys():
            response_text.append(k)
            for item in res[k]:
                response_text.append(f"• {item}")
        
        update.message.reply_text(
            telegram_escape(NEWLINE.join(response_text)),
            parse_mode=PARSEMODE_MARKDOWN_V2
        )
        return ConversationHandler.END

    
NEWLINE = "\n"    

def start(update: Update, context: CallbackContext) -> int:
    return NEXT_QUESTION

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', question)],
        states={
            NEXT_QUESTION: [MessageHandler(Filters.all, question)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()


# In[2]:





# In[ ]:





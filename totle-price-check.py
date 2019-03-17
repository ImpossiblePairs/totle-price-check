# This Telegram bot uses the Totle API to check prices of various ERC-20 tokens across multiple exchanges
# and returns the current bid and ask price data for the token and calculates potential arbitrage opportunities.
# NOTE: This code may contain errors and behave in a manner differently than intended...I'm a hobby programmer
# not a code warrior. Comments on modifications that could be made to improve this are welcome.

import requests
import json
import telegram
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import Updater

# Totle API endpoints for exchange and price data
tokenListAPI = 'https://services.totlesystem.com/tokens'
tokenPriceAPI = 'https://services.totlesystem.com/tokens/prices'
tokenExchangesAPI = 'https://services.totlesystem.com/exchanges'

# Telegram bot token
botToken = "PASTE YOUR BOT TOKEN HERE"


# Start the bot
def start(bot, update):
    output = "Welcome to Totle Price Bot!\n"
    sent = bot.sendMessage(update.message.chat.id, output)
    options(bot, sent)


# Display the list of commands the bot can process
def help_menu(bot, update):
    output = "Hi! I can respond to the following commands:\n"
    output += "/options - Button-based navigation menu\n"
    output += "/check <TokenSymbol> - Check for exchange prices and arbitrage of a specific token " \
              "(ex: /check DAI or /check to see a list of tokens)\n"
    output += "/arbitrage - Check Totle's API data for arbitrage opportunities\n"
    output += "/help - Display a list of commands I can follow\n"
    output += "/start - Commence or recommence operation of TotleXPbot\n"
    bot.sendMessage(chat_id=update.message.chat.id, text=output)

	
# Create the keyboard for button based navigation of bot
def options(bot, update):
    kb = [[
            telegram.InlineKeyboardButton("Check for Arbitrage", callback_data="sel_arbitrage"),
            telegram.InlineKeyboardButton("Check Token Price", callback_data="sel_check")
         ]]

    reply_markup = telegram.InlineKeyboardMarkup(kb)
    if int(update.chat.id) > 0:
        chat_id = int(update.chat.id)
    else:
        chat_id = int(update.message.chat.id)

	bot.sendMessage(chat_id,
                    text="Would you like to check for arbitrage or check a specific token price? "
                         "(use /help for more options)",
                    reply_markup=reply_markup)


# Totle API request retrieval
def get_totle_api_data(requested_api_call):
    try:
        request = requests.get(requested_api_call)
        return request
    except requests.exceptions.Timeout:
        print("I'm sorry, my connection to Totle timed out. Please try again.")
    except requests.exceptions.TooManyRedirects:
        print("I'm sorry, I couldn't find the API requested. Please contact Totle support.")
    except requests.exceptions.RequestException as e:
        print("I'm sorry, there was an unexpected error when I tried to process your request. Please try again.")
        print(e)


# Retrieve a list of exchanges from Totle's Exchange API endpoint
def get_exchanges():
    response_exchange_names = get_totle_api_data(tokenExchangesAPI)
    content_exchanges = response_exchange_names.content.decode("utf8")
    exchange_list_data = json.loads(content_exchanges)
    return exchange_list_data['exchanges']


# Retrieve a list of pricing at various exchanges from Totle's Tokens API endpoint
def button_check_token_price(bot, update, token):

    name = token['name']
    symbol = token['symbol']
    contract = token['address']
    icon = token['iconUrl']
    bot.sendPhoto(update.chat.id, icon, "Results for\n{} [{}]".format(name, symbol))

    response_token_prices = get_totle_api_data(tokenPriceAPI)
    content_price = response_token_prices.content.decode("utf8")
    token_price_data = json.loads(content_price)
    output = "Totle Price Data\n\n"

	# Find the contract and retrieve token price data if found
    for tokenContract in token_price_data['response']:

        if tokenContract == contract:
            exchange_names = get_exchanges()
            token_exchange_prices = token_price_data['response'][tokenContract]

            # Set up variables for arbitrage check
            highest_bid = -99999999.000
            lowest_ask = 99999999.000
            hb_exchange = "None"
            la_exchange = "None"

            for k, v in token_exchange_prices.items():
                for exchange in exchange_names:
                    exchange_key = exchange['id']
                    if int(exchange_key) == int(k):
                        try:
                            bid = float(v['bid'])
                            ask = float(v['ask'])
                        except (TypeError, AttributeError):
                            continue
                        output += "Bid  {0:.8f}    Ask  {1:.8f}    Exchange  {2}\n".format(
                            bid, ask, exchange['name'])
                        if bid > highest_bid:
                            highest_bid = bid
                            hb_exchange = exchange['name']
                        if ask < lowest_ask:
                            lowest_ask = ask
                            la_exchange = exchange['name']

            # Check for arbitrage opportunities and report price and arbitrage results
            if highest_bid > 0:
                gap = highest_bid - lowest_ask
                gap_percent = gap / lowest_ask

                if gap > 0:
                    output += "\n{0:.2f}% Arbitrage    \n{1}  ->  {2}\n\n".format(
                        gap_percent, la_exchange, hb_exchange)
                    bot.sendMessage(chat_id=update.chat.id,
                                    text="{}".format(output))
                else:
                    output += "\nNo potential arbitrage trades found.\n"
                    bot.sendMessage(chat_id=update.chat.id,
                                    text="{}".format(output))
            else:
                output = "\nNo potential arbitrage trades found.\n"
                bot.sendMessage(chat_id=update.chat.id,
                                text="{}".format(output))
            bot.sendMessage(chat_id=update.chat.id,
                            text="Try:"
                                 "\n/help to see a list of commands"
                                 "\n/options for button-based navigation")
            return
    output += "I'm sorry, I couldn't find any exchange data. Try: "
    output += "\n/help to see a list of commands"
    output += "\n/options for button-based navigation"
    bot.sendMessage(chat_id=update.chat.id,
                    text="{}".format(output))
    return

	
# Build a keyboard button menu of tokens retrieved for the user to select
def build_token_keyboard(tokens, pos):
    kb = []

    current_position = pos
    end_position = current_position + 8
    last_token_position = len(tokens['tokens']) - 1
    if end_position > last_token_position:
        end_position = last_token_position

    while current_position <= end_position:
        kb += [[telegram.InlineKeyboardButton("{}".format(tokens['tokens'][current_position]['name']),
                                              callback_data="token_sel {}"
                                              .format(tokens['tokens'][current_position]['symbol']))]]
        current_position += 1

    if pos > 0:
        if end_position < last_token_position:
            kb += [[telegram.InlineKeyboardButton("Previous", callback_data="sel_previous {}".format(pos)),
                   telegram.InlineKeyboardButton("Close", callback_data="sel_close"),
                   telegram.InlineKeyboardButton("Next", callback_data="sel_next {}".format(end_position))]]
            token_keyboard = telegram.InlineKeyboardMarkup(kb)
            return token_keyboard
    if pos == 0:
        if end_position < last_token_position:
            kb += [[telegram.InlineKeyboardButton("Close", callback_data="sel_close"),
                    telegram.InlineKeyboardButton("Next", callback_data="sel_next {}".format(end_position))]]
            token_keyboard = telegram.InlineKeyboardMarkup(kb)
            return token_keyboard

    if pos > 0:
        kb += [[telegram.InlineKeyboardButton("Previous", callback_data="sel_previous {}".format(pos))]]

    kb += [[telegram.InlineKeyboardButton("Close", callback_data="sel_close")]]

    if end_position < last_token_position:
        kb += [[telegram.InlineKeyboardButton("Next", callback_data="sel_next {}".format(end_position))]]

    token_keyboard = telegram.InlineKeyboardMarkup(kb)
    return token_keyboard


# Handle keyboard button selection
def callback_query_handler(bot, update):
    cqd = update.callback_query.data

    if cqd == "sel_arbitrage":
        bot.deleteMessage(update.callback_query.message.chat.id,
                          update.callback_query.message.message_id)
        bot.sendMessage(update.callback_query.message.chat.id, "Ok, checking for arbitrage now.")
        button_arbitrage(bot, update)

    if cqd == "sel_check":
        bot.deleteMessage(update.callback_query.message.chat.id,
                          update.callback_query.message.message_id)
        sent = bot.sendMessage(update.callback_query.message.chat.id, "Ok, retrieving the token list for you.")
        reply = button_check_token()

        try:
            keyboard = build_token_keyboard(reply, 0)
            bot.editMessageText(chat_id=sent.chat.id,
                                message_id=sent.message_id,
                                text="Please select a token from the menu below"
                                     ", or if you know the token you wish to check type: /check <TokenSymbol>\n"
                                     "example: /check DAI",
                                reply_markup=keyboard)
        except Exception as e:
            print(e)

    if cqd == "sel_close":
        bot.deleteMessage(update.callback_query.message.chat.id,
                          update.callback_query.message.message_id)
        bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                        text="Token selection menu closed. Try:"
                             "\n/help to see a list of commands"
                             "\n/options for button-based navigation")

    tokens = retrieve_tokens()

    if "sel_previous" in cqd:
        pos = int(cqd.split()[1]) - 9
        keyboard = build_token_keyboard(tokens, pos)
        bot.edit_message_reply_markup(chat_id=update.callback_query.message.chat.id,
                                      message_id=update.callback_query.message.message_id,
                                      reply_markup=keyboard)
        return

    if "sel_next" in cqd:
        pos = int(cqd.split()[1]) + 1

        keyboard = build_token_keyboard(tokens, pos)
        bot.edit_message_reply_markup(chat_id=update.callback_query.message.chat.id,
                                      message_id=update.callback_query.message.message_id,
                                      reply_markup=keyboard)
        return

    if "token_sel" in cqd:
        cqd = cqd.split()[1]
        for token in tokens['tokens']:
            if cqd == token['symbol']:
                bot.deleteMessage(update.callback_query.message.chat.id,
                                  update.callback_query.message.message_id)
                bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                                text="Checking token prices for {} [{}]\n"
                                     "This may take a few moments..."
                                .format(token['name'], token['symbol']))
                button_check_price(bot, update, token['address'])


# Call to retrieve the token list from Totle's Tokens API endpoint on button press
def button_check_token():
    try:
        tokens = retrieve_tokens()
        return tokens
    except Exception as e:
        print(e)


# Call to retrieve any arbitrage opportunities from Totle's API endpoints on button press
def button_arbitrage(bot, update):
    output = "Ok, checking with Totle for arbitrage opportunities now..."

    try:
        if not update['callback_query']:
            sent = bot.sendMessage(update.message.chat.id, output)
        else:
            sent = bot.sendMessage(update.callback_query.message.chat.id, output)
        button_retrieve_totle_data(bot, sent, "")
    except Exception as e:
        print(e)


# Call to check the price of a specific token using Totle's Tokens API endpoint
def button_check_price(bot, update, contract):
    try:
        sent = check_type(bot, update)
        button_retrieve_totle_data(bot, sent, contract)
    except Exception as e:
        print(e)


# Retrieve Totle Token's API data
def retrieve_tokens():
    response_token_list = get_totle_api_data(tokenListAPI)
    content_token_list = response_token_list.content.decode("utf8")
    token_list_data = json.loads(content_token_list)
    return token_list_data


# Retrieve all of Totle's token API endpoints
# Then, check the price of a token if one is submitted
# Otherwise, search for arbitrage
def button_retrieve_totle_data(bot, update, args):

    # Retrieve token list
    response_token_list = get_totle_api_data(tokenListAPI)
    content_token_list = response_token_list.content.decode("utf8")
    token_list_data = json.loads(content_token_list)

    # Retrieve token price data
    response_token_prices = get_totle_api_data(tokenPriceAPI)
    content_price = response_token_prices.content.decode("utf8")
    token_price_data = json.loads(content_price)

    # Retrieve exchange price data
    response_exchange_names = get_totle_api_data(tokenExchangesAPI)
    content_exchanges = response_exchange_names.content.decode("utf8")
    exchange_list_data = json.loads(content_exchanges)

    if len(args) > 0:
        for token in token_list_data['tokens']:
            if token['address'] == args:
                button_check_token_price(bot, update, token)
                break
    else:
        button_check_for_arbitrage(bot, token_list_data, token_price_data, exchange_list_data, update)
        bot.sendMessage(chat_id=update.chat.id, text="Arbitrage check completed. Try:"
                                                     "\n/help to see a list of commands"
                                                     "\n/options for button-based navigation")


# Retrieve arbitrage opportunities and display results
def button_check_for_arbitrage(bot, token_list, token_prices, exchange_list, update):

    output = ""
    exchange_names = exchange_list['exchanges']

    for token in token_list['tokens']:
        token_name = token['name']
        token_symbol = token['symbol']
        token_contract = token['address']
        token_icon = token['iconUrl']

        try:
            token_exchange_prices = token_prices['response'][token_contract]

            highest_bid = -99999999.000
            lowest_ask = 99999999.000
            hb_exchange = "None"
            la_exchange = "None"

            for k, v in token_exchange_prices.items():
                for exchange in exchange_names:
                    exchange_key = exchange['id']
                    if int(exchange_key) == int(k):
                        if float(v['bid']) > float(highest_bid):
                            highest_bid = float(v['bid'])
                            hb_exchange = exchange['name']
                        if float(v['ask']) < float(lowest_ask):
                            lowest_ask = float(v['ask'])
                            la_exchange = exchange['name']

            output_length = len(output) + len(token_name) + len(token_symbol) + len(token_exchange_prices)

            gap = highest_bid - lowest_ask
            arbitrage_percent = gap / lowest_ask * 100
            if gap > 0:
                if la_exchange == hb_exchange:
                    print("Possible price error for {} [{}] (arbitrage on same exchange unlikely.)"
                          .format(token_name, token_symbol))
                else:
                    if output_length < 2048:

                        # Compile and send the arbitrage data to Telegram
                        output = "{} [{}]\n".format(token_name, token_symbol)
                        output += "{:.1f}% Arbitrage\n\n".format(arbitrage_percent)
                        output += "Buy [{}]\n{}\n\n".format(la_exchange, '{:.8f}'.format(lowest_ask))
                        output += "Sell [{}]\n{}\n\n".format(hb_exchange, '{:.8f}'.format(highest_bid))
                        bot.sendPhoto(update.chat.id, token_icon, output)
                    else:
                        output = "{} [{}]\n".format(token_name, token_symbol)
                        output += "{:.1f}% Arbitrage\n\n".format(arbitrage_percent)
                        output += "Buy [{}]\n{}\n\n".format(la_exchange, '{:.8f}'.format(lowest_ask))
                        output += "Sell [{}]\n{}\n\n".format(hb_exchange, '{:.8f}'.format(highest_bid))
                        bot.sendPhoto(update.chat.id, token_icon, output)
        except Exception as e:
            if str(e).strip("'") == token_contract:
                print("Couldn't find price data for {} [{}] [{}]".format(
                    token_name, token_symbol, e))
            else:
                print(e)

				
# Check the type of Telegram update to set the correct chat id for bot responses
def check_type(bot, update):
    output = "Retrieving data from Totle now..."

    if type(update) is telegram.update.Update:
        sent = bot.sendMessage(update.callback_query.message.chat.id, output)
        return sent
    if type(update) is telegram.message.Message:
        sent = bot.sendMessage(update.chat.id, output)
        return sent


# Handle user typed "check" command
def check_price(bot, update, args):
    try:
        if not args:
            sent = bot.sendMessage(update.message.chat.id, "Ok, retrieving the token list for you.")
            reply = button_check_token()
            try:
                keyboard = build_token_keyboard(reply, 0)
                bot.editMessageText(chat_id=sent.chat.id,
                                    message_id=sent.message_id,
                                    text="Please select a token from the menu below"
                                         ", or if you know the token you wish to check type: /check <TokenSymbol>\n"
                                         "example: /check DAI",
                                    reply_markup=keyboard)
            except Exception as e:
                print(e)
        else:
            tokens = retrieve_tokens()
            symbol = args[0].upper()
            found = 0
            for token in tokens['tokens']:
                if symbol == token['symbol']:
                    found = 1
                    sent = bot.sendMessage(chat_id=update.message.chat.id,
                                           text="Found it!\n\nChecking token prices for {} [{}]\n"
                                                "This may take a few moments..."
                                                .format(token['name'], token['symbol']))
                    button_check_price(bot, sent, token['address'])
            if found == 0:
                bot.sendMessage(update.message.chat.id, "Sorry, I couldn't find any data for {}.".format(symbol))
        return
    except RuntimeError:
        output = "Sorry, I couldn't understand your request. Please use another command.\n"
        output += "For a list of commands type /help)\n"
        bot.sendMessage(update.message.chat.id, output)


# Telegram bot operations
def main():
    # Set the updater
    bot_updater = Updater(botToken)

    # Set the dispatcher to register the command handlers for Telegram
    bot_dispatch = bot_updater.dispatcher

    # Register the Telegram command handlers
    bot_dispatch.add_handler(CommandHandler("start", start))
    bot_dispatch.add_handler(CommandHandler("help", help_menu))
    bot_dispatch.add_handler(CommandHandler("options", start))
    bot_dispatch.add_handler(CommandHandler("check", check_price, pass_args=True))
    bot_dispatch.add_handler(CommandHandler("arbitrage", button_arbitrage))

    # Start checking updates
    bot_dispatch.add_handler(MessageHandler(Filters.text, options))
    bot_dispatch.add_handler(MessageHandler(Filters.text, check_price))
    bot_dispatch.add_handler(MessageHandler(Filters.text, button_arbitrage))
    bot_dispatch.add_handler(telegram.ext.CallbackQueryHandler(callback_query_handler))

    # Start the bot
    bot_updater.start_polling(poll_interval=0.0, timeout=10, clean=True)
    bot_updater.idle()

# GO
if __name__ == '__main__':
    main()

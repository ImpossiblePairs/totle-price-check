# totle-price-check
A minimal Telegram bot that utilises Totle's API data to report the price of ERC-20 tokens across multiple exchanges and compare the prices to determine if there is any potential for arbitrage trading. Available user functions include typed commands or button-based navigation.

# Implementation instructions
The following instructions were current at time of commit
Lines with "/" preceeding them are an input command for Telegram to be typed into the message window and sent
Lines beneath an input command are to be entering into telegram in a single message (i.e. all lines of text before pressing the send button)

**PART ONE: Implement Telegram Bot**
1. Add BotFather: Search for @BotFather, then select "start" to interact with it
2. Create a new bot: type **/newbot**
3. Enter a name for your bot: <your_bot_name_here> (example "totlePriceChecker")
4. Enter username for your bot: <your_bot_name_here>bot (example "totlePriceCheckerbot")
5. Retrieve Access Token: Copy and save the access token displayed (required for code interaction)
6. Set the bot's "About" description: type **/setabout** then a short description (example: "This is an arbitrage and price checking bot for ERC-20 tokens")
8. Set the bot's "Description": type **/setdescription** then add a longer description (example: "This bot uses Totle's APIs to check the buy (bid) and sell (ask) prices for a range of ERC-20 token across multiple DEXs.")
9. Set the bot's commands: type **/setcommands** then add the commands and descriptions (example: **check** - Check and report the price and potential for arbitrage of an ERC-20 token that Totle tracks over multiple DEXs)


**PART TWO: Initiate Bot Code**
1. Save **totle-price-check.py** to a relevant location
3. Using your preferred editor, update python variable **botToken** on line 20 with your Access Token (Part One: Step 5)
4. Save and **run totle-telegram-price-bot.py**


**PART THREE: Usage**
1. Open Telegram
2. Search in Telegram for your bot (@<your_bot_name>, then select "start" to interact with it
3. Follow the prompts.

Enjoy!

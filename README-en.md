# Telegram Grabber v2.3 2024

The bot allows you to send all content from any telegram channel (if the channel admin has not prohibited copying content) to your channel without mentioning the author of the channel. It is also possible to replace all links and mentions in posts with yours
#RoadMap
- [x] 01/02/2024 Added an inline menu, moderation mode, rebooting the bot from the online menu, adding channels without commands (by clicking on the inline menu), updated instructions

- [x] 01/09/2024 Added the ability to add channels by @username

- [x] 01/10/2024 Set the client version during authorization to solve a possible crash problem on all devices

- [x] 01/11/2024 Fixed display of embedded links when replacing

- [x] 01/11/2024 Implementation of Chat GPT - in moderation mode added a “Text rewriting” button (Works only with single messages, if an album is sent, there will be no button (maybe I’ll add it in the future)). The text upon clicking the button will have to rewrite Chat GPT to create a unique publication.

- [x] 01/11/2024 Now all the variables that need to be changed are **filled in the config.py file**

- [x] 01/12/2024 Added a ban on all commands (/) for users whose id does not match my_id from config.py

Planned:

- [ ] Adding a blacklist of words to ignore advertising publications

- [ ] Fix a bug with the inability to forward a message if it contains a link preview

- [ ] Improve the capabilities of the command with matching bindings

- [ ] Add a replacement for the text in which the link is embedded (currently only the link is replaced)

# Libraries used

_Everything was tested on Python 3.11_

For the bot to work, you need to install libraries.

aiogram library:

     pip install aiogram==2.25.1
_(If in the future it offers to update the aiogram library, then there is no need. Everything works only on version 2.25.1)_

telethon library:
 
     pip install telethon
_Currently everything works stably on the latest version of the telethon library (1.33)_


httpx library: (proxy for Chat GPT)

     pip install httpx


# How to start

1. Create a telegram bot. To do this, you need to write to the bot [BotFather](https://telegram.me/botfather) and follow the instructions. After that, save the bot token.
2. Get api_id, api_hash. You can do this on the website [my.telegram.org](https://my.telegram.org/auth). Instructions: https://www.youtube.com/watch?v=8naENmP3rg4
3. Set the api_id, api_hash, bot_token and my_id variables in the config.py file.

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/e06a14e4-e2cc-4873-9f84-1b0ee28f654e)


take my_id from [Get My ID](https://t.me/getmyid_bot) from here (send any message to the bot, it will give you your id):

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/10a83730-3708-47d7-a134-f700ef037c4d)



Launch the bot with the command:

     python main.py

**When you first start, you need to enter the phone number and code that will be sent to telegram**

# Usage example:
1. Go to the telegram bot that we created at the beginning. Enter the command “/start”, click “Add channel” and enter the id of the channel from which you want to take content.
The id of the desired channel can be found by forwarding any message from the channel to the bot (example id for channels: -1001009232144) [Get My ID](https://t.me/getmyid_bot)
![image](https://user-images.githubusercontent.com/91873172/236866756-06b5a78f-0b58-45f2-a238-ce6e40550b8a.png)

You can also enter the username through "@", but it works more stable through id. **If it doesn’t work through id, enter @username**

2. Add a channel to which messages will be sent. To do this, click “Add recipient channel”. The bot in which we enter all this must be the administrator of this channel.
3. We indicate the correspondence between channels (this is necessary if you add several source channels and several channels where to publish, and you want publications from certain channels to come to specific channels) by writing the id of the source channel and the id of the recipient channel separated by a space with the command /set_channel_mapping (Example: /set_channel_mapping -100123132890 -1000932314321).
4. After this, we reload the code either by manually closing and opening the code compiler (the most stable) in which we are working, or by clicking the “Reload bot” button (not stable). **Now all new messages will be sent to your channel.**
5. The command is also available to you

     /last_messages number of messages or all if all
    
She sends the latest messages to your channel. If you have added several source channels, and the latest messages are needed only from one channel, then write

     /last_messages source channel id number of messages

6. Moderation mode. When moderation mode is activated, all messages will be sent first to your technical channel, where you can edit, delete and publish them:

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/cbdf1fb7-e5b0-4870-b01a-59a514785abd)


![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/d6cf2ccf-f474-4bf0-b371-d3ad3cf0c77e)


To make it work, create a new empty channel and enter the id of this channel in technical_channel_id in the config.py file. (you can get the id by analogy as with other channels). Don’t forget to assign the bot as a technical channel administrator.


If you have edited a message, then click on “Edited” so that it is updated in the repository. Possible bug: when a large number of messages accumulate in a technical channel, when you click on “Send” it may freeze. To make it work, click on “Edited” and then “Submit”.

**It is also possible to replace all links and mentions that are published on channels with yours**. In the config.py file, replace with the ones you need

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/ac6f8843-372a-4d73-8c1d-09c4a36aa491)

**Rewrite of text from Chat GPT**. In moderation mode there is a "Rewrite text" button. To make it work, fill in the proxy_url and openai_api_key in the config.py file. proxy_url must be in HTTP or HTTPS format. If you have a proxy with a login and password, then in the proxy settings set authorization to your ip.
Even if the proxy is HTTPS, there should still be http here:
![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/36bdced9-73ef-4d94-8fe5-655c02fe69a6)

openai_api_key is taken from the openai website https://platform.openai.com/api-keys if you have a budget in https://platform.openai.com/usage. If there is no proxy and openai_api_key, then leave these data empty, or you can contact me to purchase.



# List of available commands:
* /start - Start working with the bot
* /help - Get a list of available commands
* /add_channel - Add a channel for work
* /remove_channel - Remove a channel from the list
* /list_channels - Show a list of added channels
* /add_destination_channel - Add destination channel
* /remove_destination_channel - Remove the destination channel from the list
* /list_destination_channels - Show a list of destination channels
* /set_channel_mapping - Set mapping between channels
* /last_messages (number of messages or all if all) - Send the latest messages from channels


Lists of channel IDs are stored in a *.pickle file to save settings after the bot is restarted. Sending messages from technical after rebooting the bot, when moderation is enabled, will fail.

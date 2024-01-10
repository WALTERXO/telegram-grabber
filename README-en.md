# Telegram Grabber v2.1 2024
The bot allows forwarding all content from any Telegram channel (if the channel admin hasn't prohibited content copying) to your channel without mentioning the original channel's author. Additionally, there's an option to replace all links and mentions in posts with your own.

- [x] 02.01.2024 Added inline menu, moderation mode, bot reboot from the online menu, adding channels without commands (by clicking on the inline menu), updated the instructions.

- [x] 09.01.2024 Added the ability to add channels via @username.

- [x] 10.01.2024 Set the client version on authorization to resolve potential crashing issues on all devices.

Planned:

- [ ] Adding a blacklist of words to ignore advertising posts.

- [ ] Fixing the display of embedded links during replacement (currently may display incorrectly).

- [ ] Integrating Chat GPT - in moderation mode, add a "Text Rewriting" button (text upon button press will be rewritten by Chat GPT to create a unique publication).

# Used Libraries

_All tested on Python 3.11_

The bot requires the following libraries to work.

aiogram Library:

    pip install aiogram=2.25.1
_(If in the future it suggests updating the aiogram library, don't do it. Everything works only on version 2.25.1)_

telethon Library:

    pip install telethon
_Currently stable on the latest version of the telethon library (1.33)_

pickle Library:

    pip install pickle

# How to Run

1. Create a Telegram bot. To do this, message [BotFather](https://telegram.me/botfather) and follow the instructions. Save the bot's token afterward.
2. Obtain api_id and api_hash. This can be done on the [my.telegram.org](https://my.telegram.org/auth) website. Guide: [YouTube](https://www.youtube.com/watch?v=8naENmP3rg4)
3. Set the variables api_id, api_hash, and bot_token in the main.py file.

![image](https://user-images.githubusercontent.com/91873172/236864151-bc15d37b-d1dc-4abf-bdf7-71c8268d4d3f.png)

4. Replace with your account ID:

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/76fa8c23-f2c2-4890-a930-6141b4fbde77)

Get it from [Get My ID](https://t.me/getmyid_bot) here (send any message to the bot, it will give your ID):

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/10a83730-3708-47d7-a134-f700ef037c4d)

Run the bot with the command:

    python main.py

**On the first run, you'll need to input your phone number and the code sent to you via Telegram**

# Example of Use:
1. Go to the Telegram bot you created at the start. Enter the command "/start", click "Add Channel," and enter the channel ID from which you want to fetch content. You can find the necessary channel ID by forwarding any message from the channel to the bot (example ID for channels: -1001009232144) [Get My ID](https://t.me/getmyid_bot)
![image](https://user-images.githubusercontent.com/91873172/236866756-06b5a78f-0b58-45f2-a238-ce6e40550b8a.png)

You can also input a username with "@" symbol, but using the ID is more stable. **If using ID doesn't work, use @username**

2. Add the channel to which messages should be sent. To do this, click "Add Destination Channel." The bot where we input all this should be an administrator of this channel.
3. Specify the correspondence between channels (necessary if you add multiple source and destination channels and want publications from certain channels to go to specific ones) by writing the source channel ID and destination channel ID separated by a space using the /set_channel_mapping command (Example: /set_channel_mapping -100123132890 -1000932314321).
4. After that, reload the code manually by closing and reopening the code compiler (most stable) where you are working, or by using the "Restart Bot" button (less stable). **Now all new messages will be sent to your channel.**
5. You also have access to the command

    /last_messages number of messages or all, if all

It sends the latest messages to your channel. If you added multiple source channels and need the latest messages from only one channel, write

    /last_messages source channel id number of messages

6. Moderation mode. When activated, all messages will first come to your technical channel where you can edit, delete, and publish them:

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/cbdf1fb7-e5b0-4870-b01a-59a514785abd)

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/da314d89-fc1f-4d48-885b-d801ed31df1c)

To enable it, create a new empty channel and input its ID in the code (get ID similar to other channels). Don't forget to make the bot an administrator of the technical channel.

![image](https://github.com/WALTERXO/telegram-grabber/assets/91873172/a9ad67b1-2cc2-4967-9519-59a6e458588e)

If you edited the message, click on "Edited" to update it in the storage. Possible bug: when a large number of messages accumulate in the technical channel, clicking "Send" might cause it to hang. To resolve, click "Edited" and then "Send".

**You can also replace all links and mentions posted on channels with your own**. In the code editor search, find all mentions of "test" and insert what you need:

![image](https://user-images.githubusercontent.com/91873172/236871594-5904f387-637a-4df4-894e-b54c3a6ab9a6.png)
Do the same for the link:

![image](https://user-images.githubusercontent.com/91873172/236871955-47e04ae3-5db4-4f55-b2f6-f95f28b1c6e0.png)

# List of Available Commands:
* /start - Start working with the bot
* /help - Get a list of available commands
* /add_channel - Add a channel to work with
* /remove_channel - Remove a channel from the list
* /list_channels - Show a list of added channels
* /add_destination_channel - Add a destination channel
* /remove_destination_channel - Remove a destination channel from the list
* /list_destination_channels - Show a list of destination channels
* /set_channel_mapping - Set correspondence between channels
* /last_messages (number of messages or all, if all) - Send the latest messages from channels

Lists of channel identifiers are stored in a *.pickle file to retain settings after bot restart. Sending messages from the technical channel after bot restart, when moderation is on, will reset.

# Telegram Media Bot

## General
Posts images, videos and GIFs (soundless MP4s) to a specific Telegram chat from Twitter and Reddit.

### Functionality
Images and most of the videos/GIFs are shown/played inline in the chats.  
The source links are the caption of the medias. All sent links are saved in a file and every new media is checked if it was posted before (earlier runs, not actual one) and skips the file if it was posted.  
You can set two Twitter accounts and two sets of Subreddits to define which to post. "one" or "two" as command line parameter.  

#### Twitter
Creates the twitter-files and saves the IDs of the last posts of all your following accounts. On next run all the new posts since the saved IDs are posted and saves again the IDs of the last posts.

#### Reddit
Posts from all subreddits the hottest links. Gfycat and imgur links are tried to send as file for inline playback. Every Subreddit has his own configurable limit.

### Installation
* Do a virtualenv before
* ``git clone https://github.com/Nama/telegram-media-bot``
* ``source`` into your virtualenv
* ``cd telegram-media-bot``
* pip install -r requirements.txt
* python setup&#46;py install
* ``telegram-media-bot.py``
* Get the example [config] and set it to your needs

**Note**  
Not using Praw v4 since it forces me to use the closed API of Reddit.

### Usage
**Storing four files permantly, choose the working directory wisely!**
* ``telegram-media-bot.py twitter``
  * Will save Twitter data for first use
  * Executing again, will overwrite and you will miss the Twitter posts since last runtime of the script
* ``telegram-media-bot.py one``
  * Will post media from Twitter account_one
  * Will post media from subs_one
* ``telegram-media-bot.py two``
  * Will post media from Twitter account_two
  * Will post media from subs_two
* You can't use "one" and "two" at the same time

#### Cron
```
0 * * * * cd /home/bot/telegram-media-bot && /home/bot/venv/telegram-bot/bin/telegram-media-bot.py one
5 23 * * * cd /home/bot/telegram-media-bot && /home/bot/venv/telegram-bot/bin/telegram-media-bot.py two
```
* Make sure to set a working directory
* Choose the installed "binary" from your virtualenv
* "one" and "two" can be posted independant from each other with other sources (_Twitter accounts and Subreddits_)

[config]:https://github.com/Nama/telegram-media-bot/blob/master/config.json

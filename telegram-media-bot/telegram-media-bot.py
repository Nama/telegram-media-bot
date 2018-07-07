#!/usr/bin/env python

import json
import os
import praw
import requests
import tweepy
import warnings

from sys import argv
from time import sleep
from urllib import parse
from urllib import request
from urllib.error import HTTPError

# Deactivating the warnings of praw
warnings.simplefilter('ignore')

error_file = 'errors.txt'


def config_load():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

        telegram = dict()
        telegram['link'] = config['telegram']['link']
        telegram['token'] = config['telegram']['token']
        telegram['chatid'] = config['telegram']['chatid']

        reddit = dict()
        reddit['ua'] = config['reddit']['ua']
        reddit['subs_one'] = config['reddit']['subs_one']
        reddit['subs_two'] = config['reddit']['subs_two']

        twitter = dict()
        twitter['consumer_key'] = config['twitter']['consumer_key']
        twitter['consumer_secret'] = config['twitter']['consumer_secret']
        twitter['access_token'] = config['twitter']['access_token']
        twitter['access_token_secret'] = config['twitter']['access_token_secret']
        twitter['account_one'] = config['twitter']['account_one']
        twitter['account_two'] = config['twitter']['account_two']

        link_file = 'links.txt'
        return (telegram, reddit, twitter, link_file)


def posting_prepare(telegram, reddit, twitter, link_file):
    # Reddit
    connect_reddit = praw.Reddit(user_agent=reddit['ua'], check_for_updates=False)
    # Twitter
    auth = tweepy.OAuthHandler(twitter['consumer_key'], twitter['consumer_secret'])
    auth.set_access_token(twitter['access_token'], twitter['access_token_secret'])
    connect_twitter = tweepy.API(auth)

    # Files
    script_path = os.getcwd()
    media_file = 'telegram.'
    logfile = open(link_file, 'r')
    loglist = logfile.readlines()
    logfile.close()
    lastlog = ''
    for line in loglist:
        lastlog += line

    return (script_path, media_file, lastlog, connect_twitter, connect_reddit)


def save_data(arg, twitter_account, retries=0):
    with open('twitter_%s.json' % arg, 'w') as twitter_data:
        stored_data = dict()
        try:
            for user in connect_twitter.friends_ids(twitter_account):
                tweet = connect_twitter.user_timeline(count=1, id=user)
                stored_data[str(user)] = tweet[-1].id
            json.dump(stored_data, twitter_data)
        except tweepy.TweepError:
            sleep(10)
            if retries < 5:
                retries += 1
                save_data(arg, twitter_account, retries)


def send_file(method, file, media_file, link, caption, url_clean, post=None):
    filename = media_file.replace('/', '')
    f = open(filename, 'wb')
    try:
        f.write(request.urlopen(link).read())
    except HTTPError:
        f.write(request.urlopen(link.replace('.mp4', '.gif')).read())
    f.close()
    f = open(filename, 'rb')
    if post:
        text = '%s\n%s' % (post, url_clean)
    else:
        text = '%s\n%s' % (url_clean, link)
    try:
        response = requests.post('%s%s/%s' % (telegram['link'], telegram['token'], method), files={file: f}, params={'parse_mode': 'HTML', 'disable_notification': 'true', 'chat_id': telegram['chatid'], 'caption':
text})
        log = open(link_file, 'a')
        log.write(caption + '\n')
        log.close()

    except requests.exceptions.ConnectionError:
        sleep(10)
        if retries < 5:
            retries += 1
            send_link(post, retries)


def send_link(post, retries=0):
    log = open(link_file, 'a')
    try:
        log.write(post.url + '\n')
    except UnicodeEncodeError:
        log.write('EncodeError\n')
    log.close()
    try:
        response = requests.post('%s%s/%s' % (telegram['link'], telegram['token'], 'sendMessage'), params={'parse_mode': 'HTML', 'disable_notification': 'true', 'chat_id': telegram['chatid'], 'text': '%s\n<a href="%s">Reddit</a>' % (post.url, post.permalink)})
    except UnicodeEncodeError:
        error = open(error_file, 'a')
        error.write(caption + '\n')
        error.close()
    except requests.exceptions.ConnectionError:
        sleep(10)
        if retries < 5:
            retries += 1
            send_link(post, retries)


def check_link(post):
    if post.url not in lastlog:
        url = post.url.split('?')[0]
        if 'i.imgur.com' in post.url:
            if url.endswith(('jpg', 'jpeg')):
                link = url
                media_file = parse.urlparse(url).path
                send_file('sendPhoto', 'photo', media_file + '.jpg', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
            elif url.endswith('png'):
                link = url
                media_file = parse.urlparse(url).path
                send_file('sendPhoto', 'photo', media_file + '.png', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
            else:
                link = url.replace('gifv', 'mp4').replace('gif', 'mp4')
                media_file = parse.urlparse(url).path
                send_file('sendVideo', 'video', media_file + '.mp4', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
        elif 'imgur.com' in url:
            if url.endswith(('jpg', 'jpeg')):
                link = url
                media_file = parse.urlparse(url).path
                send_file('sendPhoto', 'photo', media_file + '.jpg', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
            elif url.endswith('png'):
                link = url
                media_file = parse.urlparse(url).path
                send_file('sendPhoto', 'photo', media_file + '.png', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
            elif url.endswith(('mp4', 'gifv')):
                link = url.replace('gifv', 'mp4').replace('gif', 'mp4')
                media_file = parse.urlparse(url).path
                send_file('sendVideo', 'video', media_file + '.mp4', link, url, link, '<a href="%s">Reddit</a>' % post.permalink)
            else:
                media_id = parse.urlparse(url)
                links = (('https://i.imgur.com' + media_id.path + '.mp4', '.mp4'), ('https://i.imgur.com' + media_id.path + '.png', '.png'), ('https://i.imgur.com' + media_id.path + '.jpeg', '.jpeg'))
                for link, end in links:
                    response = requests.get(link)
                    content_type = response.headers.get('content-type')
                    if end[1:] in content_type:
                        if end[1:] == 'mp4':
                            send_file('sendVideo', 'video', link + end, link, url, '<a href="%s">Reddit</a>' % post.permalink)
                            return
                        else:
                            send_file('sendPhoto', 'photo', link + end.replace('.jpeg', '.jpg'), link, url, '<a href="%s">Reddit</a>' % post.permalink)
                            return
                send_link(post)
        elif 'gfycat.com' in url:
            url_clean = 'https://gfycat.com/' + url.replace('fr/', '').replace('pl/', '').replace('gifs/detail/', '').split('/')[3].replace('.webm', '').replace('.mp4', '').replace('-size_restricted.gif', '').replace('.gif', '')
            try:
                link = requests.get('https://gfycat.com/cajax/get%s' % parse.urlparse(url_clean).path).json()['gfyItem']['mp4Url']
                media_file = parse.urlparse(url_clean).path
                send_file('sendVideo', 'video', media_file + '.mp4', link, url, url_clean, post='<a href="%s">Reddit</a>' % post.permalink)
            except:
                send_link(post)
        else:
            send_link(post)


def process_reddit(connect_reddit, subreddits, retries=0):
    for sub, limit in dict(subreddits).items():
        try:
            submissions = connect_reddit.get_subreddit(sub).get_hot(limit=limit)
            try:
                for post in submissions:
                    if post.url.split('?')[0] not in lastlog:
                        check_link(post)
            except praw.errors.HTTPException:
                sleep(10)
                if retries < 5:
                    retries += 1
                    process_reddit(connect_reddit, subreddits, retries)
        except requests.exceptions.HTTPError:
            sleep(10)
            if retries < 5:
                retries += 1
                process_reddit(connect_reddit, subreddits, retries)


def process_twitter(arg, connect_twitter, twitter_account, retries=0):
    with open('twitter_%s.json' % arg, 'r') as twitter_data:
        stored_data = dict()
        try:
            stored_data = json.load(twitter_data)
        except json.decoder.JSONDecodeError:
            print('Twitter file corrupted, recreating. Please restart')
            return
        try:
            twitter_ids = connect_twitter.friends_ids(twitter_account)
        except tweepy.error.TweepError:
            sleep(10)
            if retries < 5:
                retries += 1
                twitter_ids = connect_twitter.friends_ids(twitter_account)

        for user in twitter_ids:
            try:
                tweets = connect_twitter.user_timeline(since_id=stored_data[str(user)], id=user)
                for tweet in tweets:
                    try:
                        media = tweet.extended_entities.get('media', [{}])[0]
                    except:
                        media = tweet.entities.get('media', [{}])[0]
                    if media:
                        if media['display_url'] not in lastlog:
                            media_file = parse.urlparse(media['display_url']).path
                            caption = media['display_url']
                            if media['type'] == 'photo':
                                method = 'sendPhoto'
                                file = 'photo'
                                link = media['media_url']
                                filename = media_file + '.png'
                            elif media['type'] in ('video', 'animated_gif'):
                                method = 'sendVideo'
                                file = 'video'
                                filename = media_file + '.mp4'
                                for variant in media['video_info']['variants']:
                                    if variant['content_type'] == 'video/mp4':
                                        link = variant['url']
                            send_file(method, file, filename, link, caption, caption)
            except:
                # Twitter data has changed, creating new one
                print('Twitter data has changed, creating new one')
                os.remove('twitter_%s.json' % arg)


if __name__ == '__main__':
    # Check if needed files exist, maybe create them
    if not os.path.exists('twitter_one.json'):
        open('twitter_one.json', 'w')
    if not os.path.exists('twitter_two.json'):
        open('twitter_two.json', 'w')
    if not os.path.exists('links.txt'):
        open('links.txt', 'w')
    if not os.path.exists('config.json'):
        open('config.json', 'w')
        print('First, configure your settings in config.json!')
    else:
        # Check arguments for preparations
        try:
            arg = argv[1]
        except IndexError:
            arg = None
        if arg in ('one', 'two'):
            # Load config
            (telegram, reddit, twitter, link_file) = config_load()

            # Prepare API and files
            (script_path, media_file, lastlog, connect_twitter, connect_reddit) = posting_prepare(telegram, reddit, twitter, link_file)

            process_twitter(arg, connect_twitter, twitter['account_%s' % arg])
            process_reddit(connect_reddit, reddit['subs_%s' % arg])

            # Save Twitter-data
            save_data(arg, twitter['account_%s' % arg])
        elif arg == 'twitter':
            # Load config
            (telegram, reddit, twitter, link_file) = config_load()
            (script_path, media_file, lastlog, connect_twitter, connect_reddit) = posting_prepare(telegram, reddit, twitter, link_file)
            save_data('one', twitter['account_one'])
            save_data('two', twitter['account_two'])
        else:
            print('Either use "one", "two" or "twitter" as argument')

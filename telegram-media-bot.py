#!/usr/bin/env python

import os
import praw
import json
import tweepy
import requests
from sys import argv
from ftplib import FTP_TLS
from urllib import request, parse
from time import strftime, sleep


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

        ftp = dict()
        ftp['enabled'] = bool(config['ftp']['enabled'])
        ftp['server'] = config['ftp']['server']
        ftp['port'] = config['ftp']['port']
        ftp['user'] = config['ftp']['user']
        ftp['pw'] = config['ftp']['pw']
        ftp['path'] = config['ftp']['path']

        link_file = 'links.txt'
        return (telegram, reddit, twitter, ftp, link_file)
    return False


def posting_prepare(telegram, reddit, twitter, link_file):
    # Reddit
    connect_reddit = praw.Reddit(user_agent=reddit['ua'])
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


def save_data(twitter_account):
    with open('twitter.json', 'w') as twitter_data:
        stored_data = dict()
        for user in connect_twitter.friends_ids(twitter_account):
            tweet = connect_twitter.user_timeline(count=1, id=user)
            stored_data[str(user)] = tweet[-1].id
        json.dump(stored_data, twitter_data)


def send_file(method, file, media_file, link, caption):
    filename = media_file.replace('/', '')
    f = open(filename, 'wb')
    f.write(request.urlopen(link).read())
    f.close()
    f = open(filename, 'rb')
    response = requests.post('%s%s/%s' % (telegram['link'], telegram['token'], method), files={file: f}, params={'chat_id': telegram['chatid'], 'caption': caption})
    log = open(link_file, 'a')
    log.write(caption + '\n')
    log.close()

    if ftp['enabled']:
        ftp_con = FTP_TLS()
        ftp_con.connect(host=ftp['server'], port=ftp['port'])
        ftp_con.login(user=ftp['user'], passwd=ftp['pw'])
        ftp_con.cwd(ftp['path'])
        ftp_con.storbinary('STOR ' + filename, f)
    f.close()
    os.remove(filename)


def send_link(post):
    response = requests.post('%s%s/%s' % (telegram['link'], telegram['token'], 'sendMessage'), params={'chat_id': telegram['chatid'], 'text': post.url})
    log = open(link_file, 'a')
    log.write(post.url + '\n')
    log.close()


def check_link(post):
    if post.url not in lastlog:
        if 'i.imgur.com' in post.url:
            if post.url.endswith('jpg'):
                link = post.url
                media_file = parse.urlparse(post.url).path
                send_file('sendPhoto', 'photo', media_file + '.jpg', link, link)
            elif post.url.endswith('png'):
                link = post.url
                media_file = parse.urlparse(post.url).path
                send_file('sendPhoto', 'photo', media_file + '.png', link, link)
            else:
                link = post.url.replace('gifv', 'mp4').replace('gif', 'mp4')
                media_file = parse.urlparse(post.url).path
                send_file('sendVideo', 'video', media_file + '.mp4', link, link)
        elif 'imgur.com' in post.url:
            if post.url.endswith('jpg'):
                link = post.url
                media_file = parse.urlparse(post.url).path
                send_file('sendPhoto', 'photo', media_file + '.jpg', link, link)
            elif post.url.endswith('png'):
                link = post.url
                media_file = parse.urlparse(post.url).path
                send_file('sendPhoto', 'photo', media_file + '.png', link, link)
            elif post.url.endswith('mp4') or post.url.endswith('gifv'):
                link = post.url.replace('gifv', 'mp4').replace('gif', 'mp4')
                media_file = parse.urlparse(post.url).path
                send_file('sendVideo', 'video', media_file + '.mp4', link, link)
            else:
                media_id = parse.urlparse(post.url)
                links = (('https://i.imgur.com' + media_id.path + '.mp4', '.mp4'), ('https://i.imgur.com' + media_id.path + '.png', '.png'), ('https://i.imgur.com' + media_id.path + '.jpeg', '.jpeg'))
                for link, end in links:
                    response = requests.get(link)
                    content_type = response.headers.get('content-type')
                    if end[1:] in content_type:
                        if end[1:] == 'mp4':
                            send_file('sendVideo', 'video', link + end, link, link)
                            return
                        else:
                            send_file('sendPhoto', 'photo', link + end, link, link)
                            return
                send_link(post)
        elif 'gfycat.com' in post.url:
            link = requests.get('https://gfycat.com/cajax/get%s' % parse.urlparse(post.url).path).json()['gfyItem']['mp4Url']
            media_file = parse.urlparse(post.url).path
            send_file('sendVideo', 'video', media_file + '.mp4', link, post.url)
        else:
            send_link(post)


def process_reddit(connect_reddit, subreddits):
    for sub, limit in dict(subreddits).items():
        submissions = connect_reddit.get_subreddit(sub).get_hot(limit=limit)
        for post in submissions:
            if post.url not in lastlog:
                check_link(post)


def process_twitter(connect_twitter, twitter_account):
    with open('twitter.json', 'r') as twitter_data:
        stored_data = dict()
        try:
            stored_data = json.load(twitter_data)
        except json.decoder.JSONDecodeError:
            print('Twitter file corrupted, recreating. Please restart')
            return
        for user in connect_twitter.friends_ids(twitter_account):
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
                                variants = []
                                for variant in media['video_info']['variants']:
                                    if variant['content_type'] == 'video/mp4':
                                        link = variant['url']
                            send_file(method, file, filename, link, caption)
            except:
                # Twitter data has changed, creating new one
                print('Twitter data has changed, creating new one')
                os.remove('twitter.json')


if __name__ == '__main__':
    # Check if needed files exist, maybe create them
    os.chdir(os.path.dirname(argv[0]))
    if not os.path.exists('twitter.json'):
        open('twitter.json', 'w')
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
            (telegram, reddit, twitter, ftp, link_file) = config_load()

            # Prepare API and files
            (script_path, media_file, lastlog, connect_twitter, connect_reddit) = posting_prepare(telegram, reddit, twitter, link_file)

            process_twitter(connect_twitter, twitter['account_%s' % arg])
            process_reddit(connect_reddit, reddit['subs_%s' % arg])

            # Save Twitter-data
            save_data(twitter['account_%s' % arg])
        else:
            print('Either use "one" or "two" as argument')

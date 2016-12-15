from setuptools import setup, find_packages
setup(
    name='telegram-media-bot',
    version="2.1",
    packages=find_packages(),
    scripts=['telegram-media-bot/telegram-media-bot.py'],

    install_requires=['tweepy>=3.5.0', 'praw<=3.6.0', 'requests>=2.12.3'],

    author='Murat Özel',
    description='Send pictures and videos from Twitter and Reddit to a Telegram-Chat',
    license='MIT',
    keywords='reddit telegram twitter',
    url="https://blog.yamahi.eu",
)

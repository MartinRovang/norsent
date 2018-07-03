from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from unidecode import unidecode
from threading import Lock, Timer
import pandas as pd
import regex as re
from collections import Counter
import string
import pickle
import itertools
from textblob import TextBlob
import numpy as np
from googletrans import Translator
import os
import sys
import time, threading
from tabledef import *

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))

analyzer = SentimentIntensityAnalyzer()

#consumer key, consumer secret, access token, access secret.
ckey="59PYrQl6ei43Wc9TfUEjWntxA"
csecret="1J2IvXODO8bi87PS4cyRvSNuNDn8CR3ntKbLyI9kRzrjK5zAnc"
atoken="37235540-yC4FXCOrNIAipEkRe488KAu2bDU64rHJQjhTOTNZQ"
asecret="66wVazURKsc7I7sntGWP5acagmcZS3VTggVP7dzxDOhPc"

#Connect database
# conn = sqlite3.connect('twitter.db')
# c = conn.cursor()



MAX_DF_LENGTH = 100
def df_resample_sizes(df, maxlen=MAX_DF_LENGTH):
    df_len = len(df)
    resample_amt = 100
    vol_df = df.copy()
    vol_df['volume'] = 1

    ms_span = (df.index[-1] - df.index[0]).seconds * 1000
    rs = int(ms_span / maxlen)

    df = df.resample('{}ms'.format(int(rs))).mean()
    df.dropna(inplace=True)

    vol_df = vol_df.resample('{}ms'.format(int(rs))).sum()
    vol_df.dropna(inplace=True)

    df = df.join(vol_df['volume'])

    return df






lock = Lock()

class listener(StreamListener):

    data = []
    sent = []
    lock = None

    def __init__(self, lock):

        # create lock
        self.lock = lock

        # init timer for database save
        self.save_in_database()

        # call __inint__ of super class
        super().__init__()

    def save_in_database(self):

        # set a timer (1 second)
        Timer(1, self.save_in_database).start()
        conn = sqlite3.connect('twitter.db')
        c = conn.cursor()
        print(self.data)
        print(self.sent)
        with self.lock:
            if len(self.data):
                c.execute('BEGIN TRANSACTION')
                try:
                        c.executemany("INSERT INTO users (data1,sent,what) VALUES (?,?,?)", self.data)
                        conn.commit()
                        # print("test")
                except Exception as e:
                    print(str(e))
                # c.execute('COMMIT')

                self.data = []
                self.sent = []

    def on_data(self, data):
        try:
            #print('data')
            data = json.loads(data)
            # there are records like that:
            # {'limit': {'track': 14667, 'timestamp_ms': '1520216832822'}}
            if 'truncated' not in data:
                #print(data)
                return True
            if data['truncated']:
                tweet = unidecode(data['extended_tweet']['full_text'])
            else:
                tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            vs = analyzer.polarity_scores(tweet)
            sentiment = vs['compound']
            # print(sentiment)
            # print(tweet)
            # print(time_ms)
            time.sleep(2)
            #print(time_ms, tweet, sentiment)

            # append to data list (to be saved every 1 second)
            with self.lock:
                # self.data.append((time_ms))
                # print(self.data)
                # self.sent.append((sentiment))
                self.data.append((time_ms, tweet, sentiment))
        except KeyError as e:
            #print(data)
            print(str(e))
        return True




while True:

    try:
        auth = OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken, asecret)
        twitterStream = Stream(auth, listener(lock))
        twitterStream.filter(track=["Trump"])
    except Exception as e:
        print(str(e))
        time.sleep(5)


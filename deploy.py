from flask import Flask, flash, redirect, render_template, request, session, abort
import json
import sqlite3 as sql
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
# set chdir to current dir
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Unicode, UnicodeText
from sqlalchemy import create_engine, ForeignKey
from tabledef import *
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener








sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))
engine = create_engine('sqlite:///twitter.db', echo=True)
Session = sessionmaker(bind=engine)





app = Flask(__name__)




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


def foo():
    print("Started")
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
            conn = sql.connect('twitter.db')
            c = conn.cursor()
            # print(self.data)
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
                time.sleep(1)
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



# sentiment_term = "Trump"
#Start twitter threading
thread = threading.Thread(target=foo)
thread.start()

# def table_columns(db, table_name):
#     curs = db.cursor()
#     sql = "select * from %s where 1=0;" % table_name
#     curs.execute(sql)
#     return [d[0] for d in curs.description]

@app.route("/")
def main():
    try:
        # Session = sessionmaker(bind=engine)
        # s = Session()
        # query = s.query(data).filter(data.sent.in_([POST_SENT]) )
        # result = query.first()
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users",conn)
        # columns = table_columns(conn,users)
        # df = pd.read_sql("SELECT * FROM sentiment_fts fts LEFT JOIN sentiment ON fts.rowid = sentiment.id WHERE fts.sentiment_fts MATCH ? ORDER BY fts.rowid DESC LIMIT 1000", conn, params=(sentiment_term+'*',))
        # df.sort_values('unix', inplace=True)
        df['date'] = pd.to_datetime(df['data1'], unit='ms')
        df.set_index('date', inplace=True)
        init_length = len(df)
        df['sentiment_smoothed'] = df['what'].rolling(int(len(df)/5)).mean()
        df = df_resample_sizes(df)
        X = df.index
        Y = df.sentiment_smoothed.values
        Y2 = df.volume.values
        print(Y)
        if Y[-1] > 0:
            return render_template("oppover.html",Yverdi = Y[-1],Yvolume = Y2[-1])

        else:
            return render_template("nedover.html",Yverdi = Y[-1],Yvolume = Y2[-1])
    except Exception as e:
        print(str(e))
    return "test"








if __name__ == "__main__":
    app.run()



from flask import Flask, flash, redirect, render_template, request, session, abort, make_response, send_file
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
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Unicode, UnicodeText
from sqlalchemy import create_engine, ForeignKey
from tabledef import *
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from io import BytesIO
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import datetime
import base64
from time import gmtime, strftime



sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))
engine = create_engine('sqlite:///twitter.db', echo=True)
Session = sessionmaker(bind=engine)








app = Flask(__name__)

def movingavarage(values,window):
	weights = np.repeat(1.0,window)/window
	smas = np.convolve(values,weights,'valid')
	return smas


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


    #Connect database
    # conn = sqlite3.connect('twitter.db')
    # c = conn.cursor()



    lock = Lock()

    class listener(StreamListener):
        xz=[]
        yz=[]
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
            Timer(3, self.save_in_database).start()
            conn = sql.connect('twitter.db')
            c = conn.cursor()
            with self.lock:
                if len(self.data):
                    c.execute('BEGIN TRANSACTION')
                    try:
                            c.executemany("INSERT INTO users (data1,sent,what) VALUES (?,?,?)", self.data)
                            conn.commit()
                            print("INSERTS DATA")
                            # print("test")
                    except Exception as e:
                        print(str(e))
                    # c.execute('COMMIT')

                    self.data = []
                    self.sent = []

        def on_data(self, data):
            try:
                data = json.loads(data)
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
                time.sleep(1)
                with self.lock:
                    self.data.append((time_ms, tweet, sentiment))
            except KeyError as e:
                #print(data)
                print(str(e))
            return True



    while True:

        try:
            auth = OAuthHandler(os.environ.get('ckey'), os.environ.get('csecret'))
            auth.set_access_token(os.environ.get('atoken'), os.environ.get('asecret'))
            twitterStream = Stream(auth, listener(lock))
            twitterStream.filter(track=["Trump","Twitter"])
        except Exception as e:
            print(str(e))
            time.sleep(5)




@app.route("/tweet")
def chart():
    try:
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users",conn)
        G = df['what'].astype(float).values
        df.sort_values('data1', inplace=True)
        df['date'] = pd.to_datetime(df['data1'], unit='ms')
        df.set_index('date', inplace=True)
        init_length = len(df)
        df['sentiment_smoothed'] = df['what'].rolling(int(len(df)/5)).mean()
        df = df_resample_sizes(df,maxlen=100)
        X = df.index
        Y = df.sentiment_smoothed.values
        Y2 = df.volume.values
        # sent = [408,547,675,734]
        # values = [408,547,675,734]
        labels = -np.round(np.linspace(len(Y2)/60,0,len(Y2)),2)
        # if len(B) < len(Y):
        #     L = strftime('%H:%M', gmtime())
        #     print(L)
        #     B.append(L)
        #     print(B)
        # if len(B) == len(Y):
        #     B = [w.replace(':', '.') for w in B]
        #     B = np.array(B)
        #     labels = B.astype(float)
        #     print(labels)
        return render_template('chart.html', vol=Y2 ,sent = Y ,labels = labels)
    except Exception as e:
        print(str(e))








@app.route('/')
def home():
    chart()
    conn = sql.connect("twitter.db")
    df = pd.read_sql("SELECT * FROM users",conn)
    df['Trump'] = df['sent'].str.contains('Trump')
    df['Twitter'] = df['sent'].str.contains('Twitter')
    G = df['Trump'].astype(float).values
    Gtw = df['Twitter'].astype(float).values
    df.sort_values('data1', inplace=True)
    df['date'] = pd.to_datetime(df['data1'], unit='ms')
    df.set_index('date', inplace=True)
    init_length = len(df)
    df['sentiment_smoothed'] = df['Trump'].rolling(int(len(df)/5)).mean()
    df['sentiment_smoothedtw'] = df['Twitter'].rolling(int(len(df)/5)).mean()
    df = df_resample_sizes(df,maxlen=125)
    X = df.index
    Y = df.sentiment_smoothed.values
    Ytw = df.sentiment_smoothedtw.values
    Y2 = df.volume.values
    df['Trend'] = Y
    df['Trendtw'] = Ytw
    print(df['Trend'].values)
    print(df['Trendtw'].values)
    if abs(df['Trend'].values[0]) < abs(df['Trend'].values[-1]):
        change = abs(df['Trend'].values[-1])-abs(df['Trend'].values[0])
        if abs(df['Trendtw'].values[0]) < abs(df['Trendtw'].values[-1]):
            changetw = abs(df['Trendtw'].values[-1])-abs(df['Trendtw'].values[0])
            twitterlink = 'https://i.imgur.com/6OVin7T.png'
        else:
            twitterlink = 'https://i.imgur.com/LpNWTl2.png'
        return render_template("index.html", change = '%.4f'%change,Trumplink = 'https://i.imgur.com/6OVin7T.png', changetw = '%.4f'%changetw,twitterlink = twitterlink)
    else:
        if abs(df['Trendtw'].values[0]) < abs(df['Trendtw'].values[-1]):
            changetw = abs(df['Trendtw'].values[-1])-abs(df['Trendtw'].values[0])
            twitterlink = 'https://i.imgur.com/6OVin7T.png'
        else:
            changetw = abs(df['Trendtw'].values[-1])-abs(df['Trendtw'].values[0])
            twitterlink = 'https://i.imgur.com/LpNWTl2.png'
        change = abs(df['Trend'].values[-1])-abs(df['Trend'].values[0])
        return render_template("index.html", change = '%.4f'%change,Trumplink = 'https://i.imgur.com/LpNWTl2.png', changetw = '%.4f'%changetw,twitterlink = twitterlink)



@app.route('/kontakt')
def kontakt():
    return render_template("kontakt1.html")


thread = threading.Thread(target=foo)
thread.start()


if __name__ == "__main__":

    app.run()



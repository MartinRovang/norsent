from flask import Flask, flash, redirect, render_template, request, session, abort, make_response, send_file, jsonify, Response
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
import tweepy
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

translator = Translator()
analyzer = SentimentIntensityAnalyzer()





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

 # trump sine point, arrow, volume, color
class PersonViewModel:
    def __init__(self,points,arrow,volume,color,link,name):
        self.points = points
        self.arrow = arrow
        self.volume = volume
        self.color = color
        self.link = link
        self.name = name
    def toJSON(self):
        # return json.dumps(self, default=lambda o: o.__dict__, 
        #     sort_keys=True, indent=4)
        return {
            "points": self.points,
            "arrow": self.arrow,
            "volume": self.volume,
            "color": self.color,
            "link": self.link,
            "name": self.name
        }


def foo():
    print("Started")
    sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
    os.chdir(os.path.realpath(os.path.dirname(__file__)))





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
                translations = translator.translate(str(tweet), dest='en')
                tweet = translations.text
                vs = analyzer.polarity_scores(tweet)
                sentiment = vs['compound']
                time.sleep(1)
                with self.lock:
                    self.data.append((time_ms, tweet, sentiment))
            except KeyError as e:
                print("FAILED ON_DATA %s"%e)
                print(str(e))
            return True

    while True:

        try:
            auth = OAuthHandler(os.environ.get('ckey'), os.environ.get('csecret'))
            auth.set_access_token(os.environ.get('atoken'), os.environ.get('asecret'))
            twitterStream = Stream(auth, listener(lock))
            twitterStream.filter(track=["Trump","Putin","Sylvi Listhaug","Jonas Gahr"])

        except Exception as e:
            print(str(e))
            time.sleep(5)

# auth1 = tweepy.OAuthHandler(os.environ.get('ckey'), os.environ.get('csecret'))
# auth1.set_access_token(os.environ.get('atoken'), os.environ.get('asecret'))
# api1 = tweepy.API(auth1)



def new_person(search):
    conn = sql.connect('twitter.db')
    c = conn.cursor()
    tweets = tweepy.Cursor(api1.search, q= search , tweet_mode='extended').items(1000)
    try:
        for tweet in tweets:
            data = []
            translations = translator.translate(str(unidecode(tweet.full_text)), dest='en')
            vs = analyzer.polarity_scores(translations.text)
            data.append((1, translations.text, vs['compound']))
            c.execute('BEGIN TRANSACTION')
            c.executemany("INSERT INTO users (data1,sent,what) VALUES (?,?,?)", data)
            conn.commit()
            print(data)
            print("DATA INSERT %s"%search)
    except Exception as e:
        print("FAILED %s"%e)
        pass


def floatify(lst):
    floated_list = [float(i) for i in lst]
    return floated_list

@app.route("/trump")
def chart():
    try:
        name = 'Trump'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Trump%'",conn)
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
        return render_template('chart.html', vol=Y2 ,sent = Y ,labels = labels,name = name)
    except Exception as e:
        print(str(e))
        return e


@app.route("/putin")
def chart2():
    try:
        name = 'Putin'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Putin%'",conn)
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
        print(df)
        return render_template('chart.html', vol=Y2 ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print(str(e))
        return e

def sort_values(df):
    df.sort_values('data1', inplace=True)

def toDateTime(df):
    df['date'] = pd.to_datetime(df['data1'], unit='ms')

def setIndex(df):
    df.set_index('date', inplace=True)

def averageOfX(df, x):
    df['sentiment_smoothed'] = df['what'].rolling(int(len(df)/x)).mean()

def create_person_viewmodel(averagePoints, volume,link,name):
    arrow = 'https://i.imgur.com/LpNWTl2.png'
    color = 'red'
    if averagePoints > 0:
        arrow = 'https://i.imgur.com/6OVin7T.png'
        color = 'green'
    return PersonViewModel(averagePoints, arrow, volume, color, link, name)

def create_changes_response():
    conn = sql.connect("twitter.db")
    trumpDf = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Trump%'", conn)
    putinDf = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Putin%'", conn)
    listhaugDf = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Sylvi Listhaug%'", conn)
    gahrstoreDf = pd.read_sql("SELECT * FROM users WHERE sent LIKE '%Jonas Gahr%'", conn)


    sort_values(trumpDf)
    sort_values(putinDf)
    sort_values(listhaugDf)
    sort_values(gahrstoreDf)

    toDateTime(trumpDf)
    toDateTime(putinDf)
    toDateTime(listhaugDf)
    toDateTime(gahrstoreDf)

    setIndex(trumpDf)    
    setIndex(putinDf)
    setIndex(listhaugDf)
    setIndex(gahrstoreDf)
    
    averageOfX(trumpDf, 5)
    trumpDf = df_resample_sizes(trumpDf,maxlen=100)
    X = trumpDf.index
    trumppoints = trumpDf.sentiment_smoothed.values
    
    averageOfX(putinDf, 5)
    putinDf = df_resample_sizes(putinDf,maxlen=100)
    putinDf = putinDf.dropna()

    putinpoints = putinDf.sentiment_smoothed.values

    putinVolume = int(np.sum(putinDf.volume.values))
    trumpVolume = int(np.sum(trumpDf.volume.values))

    trumpAveragePoints = float('%.4f'%np.mean(trumppoints))
    putinAveragePoints = float('%.4f'%np.mean(putinpoints))

    listhaugAveragePoints = float('%.4f'%np.mean(floatify(listhaugDf['what'].values)))
    listhaugVolume = len(floatify(listhaugDf['what'].values))

    gahrstoreAveragePoints = float('%.4f'%np.mean(floatify(gahrstoreDf['what'].values)))
    gahrstoreVolume = len(floatify(gahrstoreDf['what'].values))

    trumpViewModel = create_person_viewmodel(trumpAveragePoints, trumpVolume,'https://norsent.herokuapp.com/trump','Trump')
    putinViewModel = create_person_viewmodel(putinAveragePoints, putinVolume,'https://norsent.herokuapp.com/putin','Putin')
    listhaugViewModel = create_person_viewmodel(listhaugAveragePoints, listhaugVolume,'https://norsent.herokuapp.com','Sylvi Listhaug')
    gahrstoreViewModel = create_person_viewmodel(gahrstoreAveragePoints, gahrstoreVolume,'https://norsent.herokuapp.com','Jonas Gahr Støre')
    
    return [trumpViewModel.toJSON(), putinViewModel.toJSON(), listhaugViewModel.toJSON(), gahrstoreViewModel.toJSON()]

@app.route('/api/changes')
def changes():
    persons = {"persons": create_changes_response()}
    return jsonify(persons)

@app.route('/')
def home():

    return render_template("index.html")


@app.route('/kontakt')
def kontakt():

    return render_template("kontakt1.html")





# def load_persons():
#     new_person("Listhaug")

# def load_persons2():
#     new_person("Jonas Gahr")


thread = threading.Thread(target=foo)
thread.start()




# thread2 = threading.Thread(target=load_persons)
# thread2.start()

# thread3 = threading.Thread(target=load_persons2)
# thread3.start()




 
if __name__ == "__main__":

    app.run()



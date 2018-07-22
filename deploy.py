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



def new_person(search):
    conn = sql.connect('twitter.db')
    c = conn.cursor()
    tweets = tweepy.Cursor(api1.search, q= search , tweet_mode='extended').items(1000)
    c.execute("DELETE FROM users WHERE sent LIKE '%"+search+"%'")
    try:
        for tweet in tweets:
            data = []
            translations = translator.translate(str(unidecode(tweet.full_text)), dest='en')
            vs = analyzer.polarity_scores(translations.text)
            data.append((1, str(unidecode(tweet.full_text)), vs['compound']))
            c.executemany("INSERT INTO users (data1,sent,what) VALUES (?,?,?)", data)
            conn.commit()
            print("DATA INSERT %s"%search)
            print(str(unidecode(tweet.full_text)))
            
    except Exception as e:
        print("FAILED %s"%e)
        pass


# new_person("Jonas Gahr støre")
# new_person("Sylvi Listhaug")
# new_person("Arbeiderpartiet")
# new_person("Fremskrittspartiet")


def foo():

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
                            print("INSERTS")
                            conn.commit()
                            conn.close()

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
                tweettrans = translations.text
                vs = analyzer.polarity_scores(tweettrans)
                sentiment = vs['compound']
                time.sleep(1)
                print(tweet)
                print(sentiment)
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
            twitterStream.filter(track=["Sylvi Listhaug","SylviListhaug","Listhaug","Jonas Gahr Støre","Jonas Støre","Jonas Gahr","Arbeiderpartiet", "Fremskrittspartiet"])


        except Exception as e:
            print(str(e))
            time.sleep(5)




def cleanup(df):
    newlist = []
    for i in df:
        if i not in newlist:
            newlist.append(i)
    return newlist


def floatify(lst):
    floated_list = [float(i) for i in lst]
    # floated_list = cleanup(floated_list)
    return floated_list


@app.route("/Arbeiderpartiet")
def chart():
    try:
        name = 'Arbeiderpartiet'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Arbeiderpartiet%' OR sent LIKE '%AP%') ",conn)
        Y = floatify(df['what'].values)[-100:]
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e



@app.route("/Fremskrittspartiet")
def chart2():
    try:
        name = 'Fremskrittspartiet'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Fremskrittspartiet%' OR sent LIKE '%frp%')",conn)
        Y = floatify(df['what'].values)[-100:]
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/store")
def chart3():
    try:
        name = 'Jonas Gahr Støre'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Jonas Gahr Store%' OR sent LIKE '%Gahr%') " ,conn)
        Y = floatify(df['what'].values)[-100:]
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/listhaug")
def chart4():
    try:
        name = 'Sylvi Listhaug'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sylvi Listhaug%' OR sent LIKE '%Listhaug%' OR sent LIKE '%SylviListhaug%' ) ",conn)
        Y = floatify(df['what'].values)[-100:]
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e




def create_person_viewmodel(averagePoints, volume,link,name):
    arrow = 'https://i.imgur.com/LpNWTl2.png'
    color = 'red'
    if averagePoints > 0:
        arrow = 'https://i.imgur.com/6OVin7T.png'
        color = 'green'
    return PersonViewModel(averagePoints, arrow, volume, color, link, name)

def create_changes_response():
    conn = sql.connect("twitter.db")
    ArbeiderpartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Arbeiderpartiet%' OR sent LIKE '%AP%') ", conn)
    FremskrittspartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Fremskrittspartiet%' OR sent LIKE '%frp%')", conn)
    listhaugDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sylvi Listhaug%' OR sent LIKE '%Listhaug%' OR sent LIKE '%SylviListhaug%' ) ", conn)
    gahrstoreDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Jonas Gahr Store%' OR sent LIKE '%Gahr%') ", conn)


    FremskrittspartietVolume = len(floatify(FremskrittspartietDf['what'].values))
    ArbeiderpartietVolume = len(floatify(ArbeiderpartietDf['what'].values))

    ArbeiderpartietAveragePoints = float('%.4f'%np.mean(floatify(ArbeiderpartietDf['what'].values)))
    FremskrittspartietAveragePoints = float('%.4f'%np.mean(floatify(FremskrittspartietDf['what'].values)))

    listhaugAveragePoints = float('%.4f'%np.mean(floatify(listhaugDf['what'].values)))
    listhaugVolume = len(floatify(listhaugDf['what'].values))

    gahrstoreAveragePoints = float('%.4f'%np.mean(floatify(gahrstoreDf['what'].values)))
    gahrstoreVolume = len(floatify(gahrstoreDf['what'].values))

    ArbeiderpartietViewModel = create_person_viewmodel(ArbeiderpartietAveragePoints, ArbeiderpartietVolume,'https://norsent.herokuapp.com/Arbeiderpartiet','Arbeiderpartiet')
    FremskrittspartietViewModel = create_person_viewmodel(FremskrittspartietAveragePoints, FremskrittspartietVolume,'https://norsent.herokuapp.com/Fremskrittspartiet','Fremskrittspartiet')
    listhaugViewModel = create_person_viewmodel(listhaugAveragePoints, listhaugVolume,'https://norsent.herokuapp.com/listhaug','Sylvi Listhaug')
    gahrstoreViewModel = create_person_viewmodel(gahrstoreAveragePoints, gahrstoreVolume,'https://norsent.herokuapp.com/store','Jonas Gahr Støre')
    
    return [ArbeiderpartietViewModel.toJSON(), FremskrittspartietViewModel.toJSON(), listhaugViewModel.toJSON(), gahrstoreViewModel.toJSON()]



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



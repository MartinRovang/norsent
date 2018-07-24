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
    def __init__(self,points,arrow,volume,color,link,name,icon):
        self.points = points
        self.arrow = arrow
        self.volume = volume
        self.color = color
        self.link = link
        self.name = name
        self.icon = icon
    def toJSON(self):
        # return json.dumps(self, default=lambda o: o.__dict__, 
        #     sort_keys=True, indent=4)
        return {
            "points": self.points,
            "arrow": self.arrow,
            "volume": self.volume,
            "color": self.color,
            "link": self.link,
            "name": self.name,
            "icon": self.icon
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
# new_person("Høyre")
# new_person("Erna Solberg")
# new_person("rødt")
# new_person("Kristelig folkeparti")
# new_person("Knut Arild Hareide")
# new_person("Bjørnar Moxnes")
# new_person("Senterpartiet")
# new_person("Trygve Slagsvold Vedum")
# new_person("Sosialistisk Venstreparti")
# new_person("Audun Lysbakken")
# new_person("Venstre")
# new_person("Trine Skei Grande")




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
            twitterStream.filter(track=["Sylvi Listhaug","SylviListhaug","Listhaug","Jonas Gahr Støre","Jonas Støre","Jonas Gahr","Arbeiderpartiet", "Fremskrittspartiet" \
            , "Høyre","Erna Solberg", "ErnaSolberg," "Rødt", "KRF","Kristelig Folkeparti", "Knut Arild Hareide", "Miljøpartiet De Grønne", "Bjørnar Moxnes"\
            , "Senterpartiet", "Sosialistisk Venstreparti", "Audun Lysbakken","AudunLysbakken", "Venstre", "Trine Skei Grande","TrineSkeiGrande"])


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
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Arbeiderpartiet%' OR sent LIKE 'A%P' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
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
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
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
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/rodt")
def chart4():
    try:
        name = 'Rødt'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Rodt%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/krf")
def chart5():
    try:
        name = 'Kristelig Folkeparti'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Kristelig Folkeparti%' OR sent LIKE '%KRF%') ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/mdg")
def chart6():
    try:
        name = 'Miljøpartiet De Grønne'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Miljopartiet De Gronne%' OR sent LIKE 'MD%G') ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/sp")
def chart7():
    try:
        name = 'Senterpartiet'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Senterpartiet%' OR sent LIKE 'S%P') ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/sv")
def chart8():
    try:
        name = 'Sosialistisk Venstreparti'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sosialistisk Venstreparti%' OR sent LIKE 'S%V') ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e



@app.route("/venstre")
def chart9():
    try:
        name = 'Venstre'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Venstre%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/erna")
def chart10():
    try:
        name = 'Erna Solberg'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Erna Solberg%' OR sent LIKE '%Erna_Solberg%' OR sent LIKE '%ErnaSolberg%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/knutarild")
def chart11():
    try:
        name = 'Knut Arild Hareide'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Knut Arild Hareide%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e


@app.route("/bjornarmox")
def chart12():
    try:
        name = 'Bjørnar Moxnes'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Bjornar Moxnes%' OR sent LIKE '%BjornarMoxnesg%' OR sent LIKE '%Bjornar_Moxnes%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e



@app.route("/audun")
def chart14():
    try:
        name = 'Audun Lysbakken'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Audun Lysbakken%' OR sent LIKE '%Audun_Lysbakken%' OR sent LIKE '%AudunLysbakken%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/tsg")
def chart15():
    try:
        name = 'Trine Skei Grande'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Trine Skei Grande%' OR sent LIKE '%TrineSkeiGrande%' OR sent LIKE '%Trine_Skei_Grande%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/listhaug")
def chart16():
    try:
        name = 'Sylvi Listhaug'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sylvi Listhaug%' OR sent LIKE '%Listhaug%' OR sent LIKE '%SylviListhaug%' ) ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e

@app.route("/hoyre")
def chart17():
    try:
        name = 'Høyre'
        conn = sql.connect("twitter.db")
        df = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Hoyre%') ",conn)
        Y = movingavarage(floatify(df['what'].values)[-500:],25)
        labels = np.linspace(len(Y),0,len(Y))
        return render_template('chart.html' ,sent = Y ,labels = labels, name = name)
    except Exception as e:
        print("Trump"+str(e)+"")
        return e



def create_person_viewmodel(averagePoints, volume,link,name,icon):
    arrow = 'https://i.imgur.com/LpNWTl2.png'
    color = 'red'
    if averagePoints > 0:
        arrow = 'https://i.imgur.com/6OVin7T.png'
        color = 'green'
    return PersonViewModel(averagePoints, arrow, volume, color, link, name, icon)

def create_changes_response_party():
    conn = sql.connect("twitter.db")

    ArbeiderpartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Arbeiderpartiet%' OR sent LIKE 'A%P') ", conn)

    FremskrittspartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Fremskrittspartiet%' OR sent LIKE '%frp%')", conn)

    hoyreDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Hoyre%') ", conn)

    rodtDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Rodt%') ", conn)

    KRFDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%KRF%' OR sent LIKE '%Kristelig Folkeparti%') ", conn)

    miljopartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Miljopartiet De Gronne%' OR sent LIKE 'M%DG' OR sent LIKE '%Miljopartiet%') ", conn)

    senterpartietDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Senterpartiet%' OR sent LIKE 'S%P') ", conn)

    sosialistiskDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sosialistisk Venstreparti%' OR sent LIKE 'S%V') ", conn)

    venstreDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Venstre%') ", conn)

    FremskrittspartietVolume = len(floatify(FremskrittspartietDf['what'].values)[-100:])
    ArbeiderpartietVolume = len(floatify(ArbeiderpartietDf['what'].values))

    hoyreDfAveragePoints = float('%.4f'%np.mean(floatify(hoyreDf['what'].values)[-100:]))
    hoyreDfVolume = len(floatify(hoyreDf['what'].values))


    rodtDfAveragePoints = float('%.4f'%np.mean(floatify(rodtDf['what'].values)[-100:]))
    rodtDfVolume = len(floatify(rodtDf['what'].values))

    KRFDfAveragePoints = float('%.4f'%np.mean(floatify(KRFDf['what'].values)[-100:]))
    KRFDfVolume = len(floatify(KRFDf['what'].values))

 
    miljopartietDfAveragePoints = float('%.4f'%np.mean(floatify(miljopartietDf['what'].values)[-100:]))
    miljopartietDfVolume = len(floatify(miljopartietDf['what'].values))

    senterpartietDfAveragePoints = float('%.4f'%np.mean(floatify(senterpartietDf['what'].values)[-100:]))
    senterpartietDfVolume = len(floatify(senterpartietDf['what'].values))

    sosialistiskDfAveragePoints = float('%.4f'%np.mean(floatify(sosialistiskDf['what'].values)[-100:]))
    sosialistiskDfVolume = len(floatify(sosialistiskDf['what'].values))

    venstreDfAveragePoints = float('%.4f'%np.mean(floatify(venstreDf['what'].values)[-100:]))
    venstreDfVolume = len(floatify(venstreDf['what'].values))


    ArbeiderpartietAveragePoints = float('%.4f'%np.mean(floatify(ArbeiderpartietDf['what'].values)[-100:]))
    FremskrittspartietAveragePoints = float('%.4f'%np.mean(floatify(FremskrittspartietDf['what'].values)[-100:]))



    #PARTIER

    ArbeiderpartietViewModel = create_person_viewmodel(ArbeiderpartietAveragePoints, ArbeiderpartietVolume,'https://norsent.herokuapp.com/Arbeiderpartiet','Arbeiderpartiet','https://i.imgur.com/Py3QHPy.png')

    FremskrittspartietViewModel = create_person_viewmodel(FremskrittspartietAveragePoints, FremskrittspartietVolume,'https://norsent.herokuapp.com/Fremskrittspartiet','Fremskrittspartiet','https://i.imgur.com/boNXCox.jpg')

    hoyreDfViewModel = create_person_viewmodel(hoyreDfAveragePoints, hoyreDfVolume,'https://norsent.herokuapp.com/hoyre','Høyre','https://i.imgur.com/Mf6mzbT.png')

    rodtDfViewModel = create_person_viewmodel(rodtDfAveragePoints, rodtDfVolume,'https://norsent.herokuapp.com/rodt','Rødt','https://i.imgur.com/MJ78NyY.png')

    KRFDfViewModel = create_person_viewmodel(KRFDfAveragePoints, KRFDfVolume,'https://norsent.herokuapp.com/krf','Kristelig Folkeparti','https://i.imgur.com/rPRFHHV.png')

    miljopartietDfViewModel = create_person_viewmodel(miljopartietDfAveragePoints, miljopartietDfVolume,'https://norsent.herokuapp.com/mdg','Miljøpartiet De Grønne','https://i.imgur.com/FOm7Pt7.png')

    senterpartietDfViewModel = create_person_viewmodel(senterpartietDfAveragePoints, senterpartietDfVolume,'https://norsent.herokuapp.com/sp','Senterpartiet','https://i.imgur.com/N81XVVC.png')

    sosialistiskDfViewModel = create_person_viewmodel(sosialistiskDfAveragePoints, sosialistiskDfVolume,'https://norsent.herokuapp.com/sv','Sosialistisk Venstreparti','https://i.imgur.com/ksmjqrO.png')

    venstreDfViewModel = create_person_viewmodel(venstreDfAveragePoints, venstreDfVolume,'https://norsent.herokuapp.com/venstre','Venstre','https://i.imgur.com/GaFFNOd.png')



    return [ArbeiderpartietViewModel.toJSON(), FremskrittspartietViewModel.toJSON(), hoyreDfViewModel.toJSON(), rodtDfViewModel.toJSON(), KRFDfViewModel.toJSON(), miljopartietDfViewModel.toJSON() \
     ,senterpartietDfViewModel.toJSON(), venstreDfViewModel.toJSON(), sosialistiskDfViewModel.toJSON()]





def create_changes_response():
    conn = sql.connect("twitter.db")

    listhaugDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Sylvi Listhaug%' OR sent LIKE '%Listhaug%' OR sent LIKE '%SylviListhaug%' ) ", conn)

    gahrstoreDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Jonas Gahr Store%' OR sent LIKE '%Gahr%') ", conn)

    ernasolbergDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Erna Solberg%' OR sent LIKE '%ErnaSolberg%'OR sent LIKE '%Erna_Solberg%') ", conn)

    knuthareideDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Knut Arild Hareide%') ", conn)

    bjornarmoxDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Bjornar Moxnes%' OR sent LIKE '%BjornarMoxnes%') ", conn)

    audunlysDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Audun Lysbakken%' OR sent LIKE '%AudunLysbakken%') ", conn)

    trinegrandeDf = pd.read_sql("SELECT * FROM users WHERE (sent LIKE '%Trine Skei Grande%' OR sent LIKE '%TrineSkeiGrande%') ", conn)


    ernasolbergDfAveragePoints = float('%.4f'%np.mean(floatify(ernasolbergDf['what'].values)[-100:]))
    ernasolbergDfVolume = len(floatify(ernasolbergDf['what'].values))

    knuthareideDfAveragePoints = float('%.4f'%np.mean(floatify(knuthareideDf['what'].values)[-100:]))
    knuthareideDfVolume = len(floatify(knuthareideDf['what'].values))

    bjornarmoxDfAveragePoints = float('%.4f'%np.mean(floatify(bjornarmoxDf['what'].values)[-100:]))
    bjornarmoxDfVolume = len(floatify(bjornarmoxDf['what'].values))

    audunlysDfAveragePoints = float('%.4f'%np.mean(floatify(audunlysDf['what'].values)[-100:]))
    audunlysDfVolume = len(floatify(audunlysDf['what'].values))

    trinegrandeDfAveragePoints = float('%.4f'%np.mean(floatify(trinegrandeDf['what'].values)[-100:]))
    trinegrandeDfVolume = len(floatify(trinegrandeDf['what'].values))

    listhaugAveragePoints = float('%.4f'%np.mean(floatify(listhaugDf['what'].values)[-100:]))
    listhaugVolume = len(floatify(listhaugDf['what'].values))

    gahrstoreAveragePoints = float('%.4f'%np.mean(floatify(gahrstoreDf['what'].values)[-100:]))
    gahrstoreVolume = len(floatify(gahrstoreDf['what'].values))

    #PARTILEDERE

    listhaugViewModel = create_person_viewmodel(listhaugAveragePoints, listhaugVolume,'https://norsent.herokuapp.com/listhaug','Sylvi Listhaug','https://upload.wikimedia.org/wikipedia/commons/c/cd/Sylvi_Listhaug_-_2014-02-13_at_18-49-18.jpg')

    gahrstoreViewModel = create_person_viewmodel(gahrstoreAveragePoints, gahrstoreVolume,'https://norsent.herokuapp.com/store','Jonas Gahr Støre','https://www.stortinget.no/Personimages/PersonImages_Large/JGS_stort.jpg')

    ernasolbergDfViewModel = create_person_viewmodel(ernasolbergDfAveragePoints, ernasolbergDfVolume,'https://norsent.herokuapp.com/erna','Erna Solberg','https://media.snl.no/system/images/55190/standard_ernasolberg2_portrett.jpg')

    knuthareideDfViewModel = create_person_viewmodel(knuthareideDfAveragePoints, knuthareideDfVolume,'https://norsent.herokuapp.com/knutarild','Knut Arild Hareide','https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Knut_Arild_Hareide_%28KrF%29.JPG/800px-Knut_Arild_Hareide_%28KrF%29.JPG')

    bjornarmoxDfViewModel = create_person_viewmodel(bjornarmoxDfAveragePoints, bjornarmoxDfVolume,'https://norsent.herokuapp.com/bjornarmox','Bjørnar Moxnes','https://upload.wikimedia.org/wikipedia/commons/e/ea/Bj%C3%B8rnar_Moxnes_2016.jpg')

    audunlysDfViewModel = create_person_viewmodel(audunlysDfAveragePoints, audunlysDfVolume,'https://norsent.herokuapp.com/audun','Audun Lysbakken','https://upload.wikimedia.org/wikipedia/commons/e/e4/Audun_Lysbakken_jamstalldhetsminister_Norge.jpg')

    trinegrandeDfViewModel = create_person_viewmodel(trinegrandeDfAveragePoints, trinegrandeDfVolume,'https://norsent.herokuapp.com/tsg','Trine Skei Grande','https://upload.wikimedia.org/wikipedia/commons/e/ed/Trine_Skei_Grande.jpg')



    return [listhaugViewModel.toJSON(),gahrstoreViewModel.toJSON(), ernasolbergDfViewModel.toJSON(), knuthareideDfViewModel.toJSON() \
    , bjornarmoxDfViewModel.toJSON() , audunlysDfViewModel.toJSON(), trinegrandeDfViewModel.toJSON()]





@app.route('/api/changes/party')
def changes():
    persons = {"persons": create_changes_response_party()}
    return jsonify(persons)


@app.route('/api/changes/leaders')
def changes1():
    persons = {"persons": create_changes_response()}
    return jsonify(persons)


@app.route('/')
def home():

    return render_template("parti.html")


@app.route('/ledere')
def home2():

    return render_template("ledere.html")



@app.route('/info')
def info():

    return render_template("info.html")


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



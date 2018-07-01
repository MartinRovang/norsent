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
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))






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



sentiment_term = "Trump"


# def table_columns(db, table_name):
#     curs = db.cursor()
#     sql = "select * from %s where 1=0;" % table_name
#     curs.execute(sql)
#     return [d[0] for d in curs.description]

@app.route("/")
def main():
    try:
        conn = sql.connect("twitter.db", check_same_thread=False)
        df = pd.read_sql("SELECT * FROM sentiment_fts fts LEFT JOIN sentiment ON fts.rowid = sentiment.id WHERE fts.sentiment_fts MATCH ? ORDER BY fts.rowid DESC LIMIT 1000", conn, params=(sentiment_term+'*',))
    # colnames = table_columns(conn, 'sentiment_fts')
    # df = pd.read_sql(
    #     "SELECT * FROM sentiment_fts " + 
    #     "sentiment_fts LEFT JOIN sentiment ON sentiment_fts.rowid = sentiment.id" + 
    #     "WHERE sentiment_fts.tweet MATCH ?" + 
    #     "ORDER BY sentiment_fts.rowid DESC LIMIT 100", conn,)
        print(df['sentiment'])
    # df.sort_values('unix', inplace=True)
    # df['date'] = pd.to_datetime(df['unix'], unit='ms')
    # df.set_index('date', inplace=True)
    # init_length = len(df)
    # df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df)/5)).mean()
    # df = df_resample_sizes(df)
    # X = df.index
    # Y = df.sentiment_smoothed.values
    # Y2 = df.volume.values
    # if Y[0] > 0:
    #     return render_template("oppover.html",Yverdi = Y[0])

    # else:
    #     return render_template("nedover.html",Yverdi = Y[0])
    except Exception as e:
        with open('errors.txt','a') as f:
            f.write(str(e))
            f.write('\n')
    return('test')




if __name__ == "__main__":
    app.run()






#!/usr/bin/env python
"""Article Count Sentiment Indexer

A script to create a sentiment index which is simply the number of news articles articles per month
"""
import os
import re
import sys
import pandas as pd
import numpy as np
import contextlib
from datetime import datetime

import sqlite3
from pathlib import Path
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from dateutil.relativedelta import relativedelta
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist

__author__ = 'Andre Bodo'
__copyright__ = 'Copyright 2020, Andre Bodo'
__credits__ = ['Andre Bodo']
__license__ = 'MIT'
__version__ = ''
__maintainer__ = 'Andre Bodo'
__email__ = 'bodo1184@mylaurier.ca'
__status__ = 'Prototype'

# Directories and file paths needed
base_path = Path(__file__).parent
dbase_loc = str(base_path) + '\\articles.db'
scowl_2of12dict = str(base_path) + '\\2of12inf.txt'
hiv_loc = str(base_path) + '\\HIV-4.csv'


# Text based progress bar from StackOverflow user Vladimir Ignatyev: https://stackoverflow.com/a/27871113 If you are
# using pycharm this function may not work as expected. To ensure it prints correctly, go to Run and make sure the
# Emulate terminal in output console is selected
def progress(count, total, prefix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write(f'{prefix}[{bar}] {percents}%\r')
    sys.stdout.flush()  # As suggested by Rom Ruben


# Load up the american word dictionary
with open(scowl_2of12dict, "r") as f:
    usa_dict = f.readlines()
usa_dict = [w.strip() for w in usa_dict]


def prepare_for_sentiment(corpus):
    s = corpus.lower().strip()
    cleaned = []

    for sent in sent_tokenize(s):
        words = word_tokenize(sent)
        p1 = re.compile(r'\$?[0-9]{1,}.?[0-9]{0,}-b?m?illion', re.IGNORECASE)  # $number.number-billions
        p2 = re.compile(r'\$[0-9]{1,}', re.IGNORECASE)  # $number
        p3 = re.compile(r'\d+-\w', re.IGNORECASE)  # remove number-words
        p4 = re.compile(r'\d+\w', re.IGNORECASE)  # remove numberwords
        p5 = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)  # urls
        p6 = re.compile(r'\d+', re.IGNORECASE)  # remove numbers

        words = [re.sub(p1, '', w) for w in words]  # billion/million
        words = [re.sub(p2, '', w) for w in words]  # $ number
        words = [re.sub(p3, '', w) for w in words]  # remove number-words
        words = [re.sub(p4, '', w) for w in words]  # remove numberwords

        words = ' '.join(words).split()
        words = [re.sub(p5, '', w) for w in words]  # urls
        words = [re.sub(p6, '', w) for w in words]  # remove numbers
        words = [w.strip() for w in words]

        # remove non-american words scowl_2of12dict
        # Word Power: A New Approach for Content Analysis
        # Narasimhan Jegadeesh
        words = [w for w in words if w in usa_dict]

        # lemmatization
        lemma = WordNetLemmatizer()
        words = [lemma.lemmatize(w) for w in words]

        # remove stopwords
        stopwords_nltk = list(stopwords.words('english'))
        words = [w for w in words if w not in stopwords_nltk]

        cleaned.append(' '.join(words))

    cleaned = ' '.join(cleaned)

    return cleaned


def term_freq(word_list):
    word_freq = {}
    for unique_word in list(set(word_list)):
        word_freq.update({unique_word: word_list.count(unique_word)})
    return word_freq


def compute_sentiment(s):
    words = word_tokenize(s)
    freq_dict = term_freq(words)
    df = pd.DataFrame(data=freq_dict.items(), columns=['terms', 'freq'])

    # sentiment score h-iv-4
    h_four = pd.read_csv(hiv_loc, usecols=[0, 2, 3])
    h_four.columns = [c.lower() for c in h_four.columns]
    h_four['entry'] = h_four['entry'].apply(lambda x: re.sub(r'\#\d+', '', x).lower())
    h_four = h_four.drop_duplicates(subset=['entry'])

    pos_terms = list(h_four.loc[~h_four['positiv'].isnull(), 'entry'].apply(str.lower))
    neg_terms = list(h_four.loc[~h_four['negativ'].isnull(), 'entry'].apply(str.lower))

    # freq (only consider the values which exist in the harvard dictionary)
    for i in range(len(df)):
        term = df.loc[df.index[i], 'terms']
        if term not in list(h_four['entry']):
            df.loc[df.index[i], 'freq'] = np.nan
    df = df.dropna()

    # sentiment (positive or negative)
    df['sentiment'] = 0
    for i in range(len(df)):
        term = df.loc[df.index[i], 'terms']
        if term in pos_terms:
            df.loc[df.index[i], 'sentiment'] = 1
        elif term in neg_terms:
            df.loc[df.index[i], 'sentiment'] = -1

    # weights
    df['weights'] = df['freq'] / df['freq'].sum()

    # sentiment score
    score = df['sentiment'] * df['weights']
    score = score.sum()

    return score


score_data = []
with contextlib.closing(sqlite3.connect(dbase_loc)) as conn:
    with conn:  # auto-commit
        with contextlib.closing(conn.cursor()) as cursor:
            # Count number of rows
            cursor.execute("SELECT COUNT(*) FROM ARTICLES")
            total_rows = int(cursor.fetchall()[0][0])
            # Get data and process it
            cursor.execute("SELECT DATE, BODY FROM ARTICLES")
            row_count = 0
            for row in cursor.fetchall():
                clean_text = prepare_for_sentiment(row[1])
                score_data.append([datetime.strptime(row[0], '%Y-%m-%d'), compute_sentiment(clean_text)])
                row_count += 1
                progress(row_count, total_rows, prefix='Processing files: ')

df = pd.DataFrame(data=score_data, columns=['date', 'score'])
df = df.groupby(by=['date'], as_index=False).sum()
df.set_index('date', inplace=True, drop=True)
df = df.resample('M').sum()

# download OVX data from yahoo finance
period1 = int(datetime.timestamp(pd.Timestamp(df.index.values[0]) - relativedelta(months=1)))
period2 = '9999999999'
base_url = 'https://query1.finance.yahoo.com/v7/finance/download'
url = f'{base_url}/^OVX?period1={period1}&period2=9999999999&interval=1d&events=history'
ovx_data = pd.read_csv(url, parse_dates=['Date'], index_col=['Date'], usecols=['Date', 'Adj Close'])
ovx_data.index.names = ['date']
ovx_data.columns = ['OVX']
ovx_data.sort_index(inplace=True)
ovx_data = ovx_data.reindex(df.index, method='ffill')

df = df.merge(ovx_data, how='inner', left_index=True, right_index=True).dropna()
df.to_excel('harvard_dict_based_index.xlsx')
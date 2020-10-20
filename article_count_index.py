#!/usr/bin/env python
"""Article Count Sentiment Indexer

A script to create a sentiment index which is simply the number of news articles articles per month
"""
import os
import re
import sys
import pandas as pd
import contextlib
from datetime import datetime
from calendar import monthrange

from dateutil.relativedelta import relativedelta
import sqlite3
from pathlib import Path

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

with contextlib.closing(sqlite3.connect(dbase_loc)) as conn:
    df = pd.read_sql('SELECT DATE FROM ARTICLES', conn, parse_dates={'DATE': '%Y-%m-%d'})

df['article_count'] = 0
df = df.groupby(by=['DATE'], as_index=False).count()
df.columns = list(map(str.lower, df.columns))
df.set_index('date', inplace=True, drop=True)
df = df.resample('M').sum()
df.sort_index(inplace=True)

# # download OVX data from yahoo finance
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

df.to_excel('count_based_index.xlsx')





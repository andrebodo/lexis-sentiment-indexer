#!/usr/bin/env python
"""Article Parser and Corpus Cleaner

A script to parse .txt files of news articles and cleanup the data for storage in an easy to access database.
"""
import os
import re
import sys
import contextlib

import sqlite3
from pathlib import Path
from dateutil.parser import parse as dateparser

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
data_path = Path(str(base_path) + '\\data\\txt\\')
dbase_loc = str(base_path) + '\\articles.db'


def extract_header(s):
    match = re.search(r'\n{4,}', s, re.IGNORECASE)
    if match:
        return s[:match.start()]
    return None


# This function is to handle the various inconsistencies with Nexis Uni data formatting.
def extract_primary_metadata(s):
    match = re.search(r'\n\scorrection\sappended', s, re.IGNORECASE)
    if match:
        return s[:match.start()]
    match = re.search(r'\ncopyright', s, re.IGNORECASE)
    if match:
        return s[:match.start()]
    return None


def extract_body(s):
    match_start = re.search(r'\n{4,}', s, re.IGNORECASE)
    match_end = re.search(r'\nlanguage:|\nclassification', s, re.IGNORECASE)
    if match_start and match_end:
        return s[match_start.end():match_end.start()]
    return None


def execute_statement(statement, data=None):
    with contextlib.closing(sqlite3.connect(dbase_loc)) as conn:
        with conn:  # auto-commit
            with contextlib.closing(conn.cursor()) as cursor:
                if data is not None:
                    cursor.execute(statement, data)
                    return cursor.fetchall()
                else:
                    cursor.execute(statement)
                    return cursor.fetchall()

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


# Main work follows
incomplete_uidx = []
incomplete_files = [f for f in data_path.rglob('idx_*_batch_*_deliverynotification.txt')]
for filepath in incomplete_files:
    m = re.match(r'(?:idx_)([0-9]+)(?:.+)', filepath.name)
    if m:
        incomplete_uidx.append(m.group(1))

print(f'There were {len(incomplete_uidx)} incomplete download files detected. ')
if incomplete_uidx:
    try:
        for i in range(len(incomplete_files)):
            incomplete_files[i].unlink(missing_ok=True)
    except (TypeError, ValueError) as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, exc_tb.tb_lineno)

    print(f'Re-scraping recommended for url indicies:\n{", ".join(incomplete_uidx)}\n'
          f'Incomplete download notification files have been deleted')

# Create a dbase if it does not exist
sql = """
CREATE TABLE IF NOT EXISTS ARTICLES(
ID INTEGER PRIMARY KEY AUTOINCREMENT, 
TITLE TEXT NOT NULL,
DATE TEXT NOT NULL, 
PUBLISHER TEXT NOT NULL,
AUTHOR TEXT, 
BODY TEXT NOT NULL,
WORDCOUNT INTEGER NOT NULL)
"""
execute_statement(sql)

# Loop through all the articles, parse and insert into database
duplicate_count = 0
all_article_files = list(data_path.rglob('*.txt'))
for idx, filepath in enumerate(all_article_files):
    try:
        with open(filepath) as f:
            content = f.read().strip()
            # Find header and extract
            header = extract_header(content)
            primary_meta = [line.rstrip() for line in extract_primary_metadata(header).splitlines() if line.strip()]
            title = primary_meta[0].strip()
            publisher = primary_meta[1].strip()
            date = primary_meta[-1].strip()

            # Parse author
            author = [line for line in header if line.lower().startswith('byline')]
            if author:
                author = re.sub(re.compile(r'byline:', re.IGNORECASE), '', author[0])
            else:
                author = None

            # Parse date
            year = re.search(r'[0-9]{4}', date).group(0)
            day = re.search(r'[0-9]{1,2}', date).group(0)
            month_pattern = re.compile(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', flags=re.IGNORECASE)
            month = re.search(month_pattern, date).group(0)
            date_str = '-'.join([year, month, day])
            date = dateparser(date_str, fuzzy=True).strftime('%Y-%m-%d')

            # Cleanup the body and determine wordcount
            body = extract_body(content)
            pattern = re.compile(r'(\w+)(?:\n|\Z)', re.IGNORECASE)
            match_idx = [m.span() for m in re.finditer(pattern, body)]
            if match_idx:
                first_match = match_idx[0]
                body = body[0:first_match[0]].replace('\n', '')

            word_count = len(body.split(' '))

            # Determine if there is a duplicate
            is_duplicate = False
            sql = """
            SELECT ID PUBLISHER, AUTHOR, WORDCOUNT FROM ARTICLES 
            WHERE TITLE=? AND DATE=? AND PUBLISHER=? AND AUTHOR=? AND WORDCOUNT=?
            """
            res = execute_statement(sql, data=[title, date, publisher, author, word_count])
            if res:
                is_duplicate = True
                duplicate_count += 1
                break

            # Insert data if it is not a duplicate
            if not is_duplicate:
                sql = """INSERT INTO ARTICLES VALUES (NULL, ?, ?, ?, ?, ?, ?)"""
                res = execute_statement(sql, data=[title, date, publisher, author, body, word_count])

            progress(idx, len(all_article_files), prefix='Processing files: ')

    except (IndexError, AttributeError, TypeError) as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, exc_tb.tb_lineno, filepath.name)
        print(header)
        break

print(f"\nCompleted processing. Number of duplicates found {duplicate_count:d} "
      f"[{duplicate_count / len(all_article_files):.1f}%].")

#!/usr/bin/env python

import string
import json
import datetime as dt
import functools
import operator
import random
from datetime import timedelta
from collections import Counter


import pandas as pd
import nltk
import plotly.offline as py
import plotly.graph_objs as go
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = stopwords.words('english')

def _get_date(datetime_str):
    return dt.datetime.strptime(datetime_str.split('T')[0], '%Y-%m-%d')

def _find_ngrams(input_list, n):
    if n > 1:
        return zip(*(input_list[i:] for i in range(n)))
    else:
        return input_list

# Create N-Gram Counters
def _get_counter_from_column(df, column_name):
    ct = Counter()
    for row in df[column_name]:
        for element in row:
            ct[element] += 1
    return ct

def _replace_count(counter, removed, added):
    counter[added] += counter[removed]
    del counter[removed]

def _avg_datetime(series):
    dt_min = series.min()
    deltas = [(x - dt_min).days for x in series]
    if len(deltas) == 0:
        print(series)
    return dt_min + timedelta(functools.reduce(operator.add, deltas) // len(deltas))

class HistoryVisualiser:

    def __init__(self, df):

        self.df = df

    def preprocess_df(self):

        wh = self.df

        # Drop columns except title and time
        wh = wh[['title', 'time']]

        # Remove expired videos
        len(wh[wh['title'].str.startswith('Watched https://www.youtube.com')]) / len(wh)

        # Remove "Watched" from title "Watched Cat Video" -> "Cat Video"
        wh['title'] = wh['title'].apply(lambda x: x[7:])

        # Remove Unavailable videos
        wh = wh.drop(wh[wh['title'].str.startswith('https://www.youtube.com')].index)

        # Lower Case "Cat Video" -> "cat video"
        wh['title'] = wh['title'].apply(lambda x: x.lower())

        # Remove whitespace
        wh['title'] = wh['title'].apply(lambda x: x.strip())
        wh['title'] = wh['title'].apply(
            lambda x: x.translate(str.maketrans(' ', ' ', string.punctuation)))

        wh['time'] = wh['time'].apply(lambda x: _get_date(x))

        self.df = wh

        return self

    def gen_ngrams(self):

        wh = self.df

        # Split words and remove stopwords
        wh['unigrams'] = wh['title'].apply(lambda x: [word for word in x.split(' ') if word not in stop_words and word != ''])
        wh['bigrams'] = wh['unigrams'].apply(lambda x: list(_find_ngrams(x, 2)))

        bag_1 = _get_counter_from_column(wh, 'unigrams')
        bag_2 = _get_counter_from_column(wh, 'bigrams')

        # Pick singular or plural for most common X words
        remove_words = []
        for word in bag_1.most_common(1000):
            word = word[0]
            if word.endswith('s'):
                singular = word[:-1]
                plural = word
            else:
                singular = word
                plural = word + 's'
            if plural in bag_1 and singular in bag_1:
                if bag_1[plural] >= bag_1[singular]:
                    remove_words.append((singular, plural))
                else:
                    remove_words.append((plural, singular))

        for (removed, added) in remove_words:
            _replace_count(bag_1, removed, added)
            wh['unigrams'] = wh['unigrams'].apply(lambda x: [added if unigram == removed else unigram for unigram in x])

        THRESHOLD = 0.3

        for bigram in bag_2.most_common(1000):
            # print("{}: {}".format(bigram[0][0], bag_1[bigram[0][0]] * 0.75))
            if (bag_1[bigram[0][0]] * THRESHOLD) <= bag_2[bigram[0]]:
                del bag_1[bigram[0][0]]
                if (bag_1[bigram[0][1]] * THRESHOLD) <= bag_2[bigram[0]]:
                    del bag_1[bigram[0][1]]
            else:
                del bag_2[bigram[0]]

        wh['ngrams'] = wh['unigrams'] + wh['bigrams']
        self.bag_1_2 = (bag_1 + bag_2)

        return self

    def get_fig(self):

        wh = self.df

        N = 100
        data = pd.DataFrame([], columns=['keyword', 'avg_datetime', 'freq'])
        for ngram in list(self.bag_1_2.most_common(N)):
            keyword = ngram[0]
            dates = wh[wh['ngrams'].apply(lambda x: (True if keyword in x else False))]['time']
            data = data.append({
                'keyword': keyword if isinstance (keyword, str) else " ".join(keyword),
                'avg_datetime': _avg_datetime(dates),
                'freq': len(dates)
            }, ignore_index=True)

        REMOVALS = []
        REMOVALS.extend([str(x) for x in list(range(100))])
        REMOVALS.extend(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])
        REMOVALS.extend(["video", "trailer", "new", "best", "official", "removed", "music", "ft", "feat"])
        REMOVALS.extend(['official video', 'official trailer', 'music video', 'official music'])
        zoom_factor = 3.5
        data = data.drop(data[data['keyword'].isin(REMOVALS)].index)
        print("before drop {}".format(len(data)))
        data = data[data.freq > zoom_factor]
        print("before drop {}".format(len(data)))
        # Plot

        palette = ['darkturquoise', 'darkorange', 'darkorchid', 'mediumseagreen', 'royalblue', 'saddlebrown', 'tomato']
        plotly_colors = [palette[random.randrange(0, len(palette))] for i in range(N)]

        trace = go.Scatter(
            x = data["avg_datetime"],
            y = [random.uniform(0, 1) for x in range(len(data))],
            mode = "text",
            text = [x.upper() for x in data["keyword"]],
            opacity=0.75,
            textfont={
                'size': [x // zoom_factor for x in list(data["freq"])],
                'color': plotly_colors,
                'family': "'Oswald', sans-serif"
            }
        )

        plot_data = [trace]
        fig = go.FigureWidget(data=plot_data)

        return fig


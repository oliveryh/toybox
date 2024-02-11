#!/usr/bin/env python
# coding: utf-8

# # Introduction

# The following learning project is intended to help me learn concepts around the steps required to create a visualisation in python, but also expose the level of information that is stored by companies such as YouTube (Google). 

# ## Objectives
# 
# * **Data Preparation:** Data preparation makes up ~80% of the work in a Data Science pipeline. I'd like to explore the best techniques to go from raw CSV data, to a cleaned up tabular format that is ready for data visualisation.
#     * [X] Data Preparation
#     * [ ]Feature Engineering
# * **Plot:** There are various modules that can be used to plot the data. I'll consider which is best for this use case, and find the best way to represent the data in hand.
#     * [ ] Plot representation within Jupyter Notebook
#     * [ ] Plot representation on webfront
# * **Web Display:** In order to display this project, what is the best way to allow users to upload their YouTube data and display the visualisation such that is can be deployed on a server with minimal effort to others.

# # Preprocessing

# ## Getting access to YouTube Data
# 
# YouTube depricated their history API due to privacy reasons a few years ago, however it's possible to download a copy of your YouTube history in a JSON format by doing the following:
# 
# 1. Go to [Google Takeout](https://takeout.google.com/)
# 2. Deselect All 
# 3. Select YouTube
# 4. Underneath YouTube, click on "All YouTube Data Included"
# 5. Deselect All
# 6. Select history
# 
# You can then download your YouTube data after it is generated and a link sent to you. You should get a file called `watch-history.json` that we'll be making use of in future steps.

# ## Data Preparation
# 
# We can take a look at the JSON and see what there is:

# In[1]:


import json
import pandas as pd

# Open History File as dataframe
file = '../watch-history.json'
with open(file, encoding='utf8') as wh_file:
    wh_dict = json.load(wh_file)
    
wh = pd.DataFrame.from_dict(wh_dict)


# In[2]:


display(wh)


# There are some parts we'd ike to make use of such as `title` that show some useful information, and others like `titleUrl` which in this project, we won't have any use for. First, we can drop everything but `title` and `time` as we don't need anything else.

# In[3]:


# Drop columns except title and time
wh = wh[['title', 'time']]


# We can see clearly that "Watched" is being prepended to the `title` field. Not only this, but where a video has become unavailable, we get a title like "Watched https://www.youtube.com/watch?v=rG5tV7zcl1s". Let's take a look at the percentage of videos that are no longer available in the dataset

# In[4]:


len(wh[wh['title'].str.startswith('Watched https://www.youtube.com')]) / len(wh)


# It's about 5%. Not too bad. Let's remove the prefix "Watched" from the titles and also drop all the unavailable videos. We'll also remove whitespace and make everything lower case for simplicitely.

# In[5]:


import string

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

wh.head()


# We only want the date from the `time` field, as the time is too granular for this particular visualisation. Let's convert this attribute to just contain a `datetime` object with the date

# In[6]:


import datetime as dt

def get_date(datetime_str):
    return dt.datetime.strptime(datetime_str.split('T')[0], '%Y-%m-%d')

wh['time'] = wh['time'].apply(lambda x: get_date(x))

wh.head()


# ## Feature Engineering
# 
# Now we have the dataframe with the important information from the original history JSON we downloaded. We're now going to add the following features in order to get a better representation of the data. We have a large collection of titles, but the title "Body Workout Exercise" and "Full Body Workout" have very similar themes, but are treated as distinct occurances unless we find some way to group entries with similar themes. We need a way to:
# 
# * Extract key themes from a video title
# * Find other videos that have this theme

# ### Keyword Analysis
# 
# In order to get aggregated meaning of the titles, we can look at the keywords in the titles.

# #### Tokenizing 
# 
# We could find the distribution of keywords such as "XBOX" or "Full-body Workout" over the range of the dataset. Notice that keywords could appear in the form of unigrams (one word) or bigrams (two words together) such as the latter example. We also want to remove stop words such as "and" and "with" in our tokens, as these won't provide any additional value to this example.

# In[7]:


import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = stopwords.words('english')

def find_ngrams(input_list, n):
    if n > 1:
        return zip(*(input_list[i:] for i in range(n)))
    else:
        return input_list

# Split words and remove stopwords
wh['unigrams'] = wh['title'].apply(lambda x: [word for word in x.split(' ') if word not in stop_words and word != ''])
wh['bigrams'] = wh['unigrams'].apply(lambda x: list(find_ngrams(x, 2)))
wh.head()


# By creating a bag of words, we can explore the frequency of the unigrams and bigrams that are appearing in the dataset.

# In[8]:


from collections import Counter

# Create N-Gram Counters
def get_counter_from_column(df, column_name):
    ct = Counter()
    for row in df[column_name]:
        for element in row:
            ct[element] += 1
    return ct

bag_1 = get_counter_from_column(wh, 'unigrams')
bag_2 = get_counter_from_column(wh, 'bigrams')

print("Bag 1\n", bag_1.most_common(10))
print("Bag 2\n", bag_2.most_common(10))


# In[9]:


print("movies: {}".format(bag_1['movies']))
print("movie: {}".format(bag_1['movie']))


# #### Combine Pluralisms
# 
# We can see from the following code snippet that a singular word's plural can appear in the bag of words together. Semantically they mean the same thing, therefore we should find a way to combine these instances. In this example, we're taking every regular noun (You just have to add s to pluralise) that has both an occurence of itself and this plural in our unigrams. We then pick one of these with the most occurances and then replace this in both the bag of words and the dataframe.

# In[10]:


# Pick singular or plural for most common 500 words
def replace_count(counter, removed, added):
    counter[added] += counter[removed]
    del counter[removed]
    
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
    replace_count(bag_1, removed, added)
    wh['unigrams'] = wh['unigrams'].apply(lambda x: [added if unigram == removed else unigram for unigram in x])
    
bag_1.most_common(10)


# In[11]:


print(bag_1['glass'])
print(bag_1['animals'])
print(bag_2[('glass', 'animals')])


# #### Duplicates in bigrams
# 
# We now also have another problem to address. If we were to combine our unigrams and bigrams now and look at the distributions of each keyword, we'd get duplicates. For example the British band "Glass Animals" appears 43 times. "glass" and "animals" occurances are largely contributed by the band's name. If we assume that if a singular word's occurs less than three times much as the respective bigram does, then it's contribution was most likely due to the bigram. Therefore we can remove it. Likewise, if the bigram appears less than a third as many times as the respective unigram, then we can remove it from the dataset.
# 
# While this is more anecdotal, this was able to extract some more of the key bigrams that I knew where in the dataset. Obviously this requires more rigor to have reproducable outcomes for other datasets.

# In[12]:


THRESHOLD = 0.3
for bigram in bag_2.most_common(1000):
    # print("{}: {}".format(bigram[0][0], bag_1[bigram[0][0]] * 0.75))
    if (bag_1[bigram[0][0]] * THRESHOLD) <= bag_2[bigram[0]]:
        del bag_1[bigram[0][0]]
        if (bag_1[bigram[0][1]] * THRESHOLD) <= bag_2[bigram[0]]:
            del bag_1[bigram[0][1]]
    else:
        del bag_2[bigram[0]]
print(bag_1[('video',)])
wh['ngrams'] = wh['unigrams'] + wh['bigrams']
bag_1_2 = (bag_1 + bag_2)


# ### Visualisation Format
# 
# We now have in our `bag_1_2` a collection of n-grams we'd like to investigate in our visulisation. Let's consider taking the most frequent `N` from this collection, and finding the mean date that they occur. By doing this, we can determine the general time of the year that videos with this feature appeared.
# 
# For this, we need to take a list of datetimes and return the average of those.

# In[13]:


import functools
import operator
from datetime import timedelta
def avg_datetime(series):
    dt_min = series.min()
    deltas = [(x - dt_min).days for x in series]
    if len(deltas) == 0:
        print(series)
    return dt_min + timedelta(functools.reduce(operator.add, deltas) // len(deltas))


# For each of these most common n-grams, let's create a new dataframe that stores the following attributes: `{keyword, average datetime, frequency of keyword}`.

# In[14]:


N = 100
data = pd.DataFrame([], columns=['keyword', 'avg_datetime', 'freq'])
for ngram in list(bag_1_2.most_common(N)):
    keyword = ngram[0]
    dates = wh[wh['ngrams'].apply(lambda x: (True if keyword in x else False))]['time']
    data = data.append({
        'keyword': keyword if isinstance (keyword, str) else " ".join(keyword),
        'avg_datetime': avg_datetime(dates),
        'freq': len(dates)
    }, ignore_index=True)


# In[15]:


data.head()


# As you can see, some of the most popular keywords relate to common suffixs of music videos or indications that the video was removed by the uploader. Therefore we'll remove a few different keywords that have no useful meaning such as "video", "official video", and numbers.

# In[16]:


REMOVALS = []
REMOVALS.extend([str(x) for x in list(range(100))])
REMOVALS.extend(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])
REMOVALS.extend(["video", "trailer", "new", "best", "official", "removed", "music", "ft", "feat"])
REMOVALS.extend(['official video', 'official trailer', 'music video', 'official music'])
data = data.drop(data[data['keyword'].isin(REMOVALS)].index)


# In[17]:


data


# In[25]:


# Plot
import random
import plotly.offline as py
import plotly.graph_objs as go
from plotly import colors


palette = ['darkturquoise', 'darkorange', 'darkorchid', 'mediumseagreen', 'royalblue', 'saddlebrown', 'tomato']
plotly_colors = [palette[random.randrange(0, len(palette))] for i in range(N)]

trace = go.Scatter(
    x = data["avg_datetime"],
    y = [random.uniform(0, 1) for x in range(len(data))],
    mode = "text",
    text = [x.upper() for x in data["keyword"]],
    opacity=0.75,
    textfont={
        'size': [x // 3.5 for x in list(data["freq"])],
        'color': plotly_colors,
        'family': "'Oswald', sans-serif"
    }
)

plot_data = [trace]
fig = go.FigureWidget(data=plot_data)
py.iplot(fig)
# py.init_notebook_mode(connected=True)
# py.iplot(plot_data, filename="test")


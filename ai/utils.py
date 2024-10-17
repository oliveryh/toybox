import re

import spacy
from names_dataset import NameDataset

# The library takes time to initialize because the database is massive. A tip is to include its initialization in your app's startup process.
nd = NameDataset()
first_names = list(nd.first_names)
last_names = list(nd.last_names)

high_rank_first_names = []
for name, name_data in nd.first_names.items():
    for country, rank in name_data['rank'].items():
        if rank < 1000:
            high_rank_first_names.append(name)
            break

high_rank_last_names = []
for name, name_data in nd.last_names.items():
    for country, rank in name_data['rank'].items():
        if rank < 1000:
            high_rank_last_names.append(name)
            break

def scrub_email_addresses(string):
    return re.sub(r'[\w\.-]+@[\w\.-]+', '<email>', string)

def _scrub_names_spacy(string):
    """
    Use a list of first names stored in first_names and a list of second names stored in last_names

    Input:
    ```
    Hi Dom

    Thanks for the help with this.

    Best,

    John
    ```

    Output:
    ```
    Hi <name>

    Thanks for the help with this.

    Best,

    <name>
    ```

    Don't use spacy, just use the lists of names
    """
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(string)
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            string = string.replace(ent.text, '<name>')
    return string


def _scrub_names_names_dataset(string):
    for name in high_rank_first_names:
        if name in string:
            string = re.sub(r'\b{}\b'.format(name), '<name>', string)
    for name in high_rank_last_names:
        if name in string:
            string = re.sub(r'\b{}\b'.format(name), '<name>', string)
    return string

def scrub_names(string):
    string = _scrub_names_spacy(string)
    string = _scrub_names_names_dataset(string)
    return string
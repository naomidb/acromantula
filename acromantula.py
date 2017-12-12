docstr = """
Acromanutla
Usage:
    acromantula.py (-h | --help)
    acromantula.py [-wd] (<input_path>)
    acromantula.py [-pd] (<input_path>)
    acromantula.py [-vd] (<input_path>)


Options:
  -h --help                     Show this message and exit
  -w --wos                      Input file is bibtex from Web of Science site
  -p --pubmed                   Input file is __ from pubmed
  -v --vivo                     Input file is csv from vivo
  -d --directory                Input is a directory of files

"""


#TODO: add config or argument for where to save database

from bibtexparser import loads
import csv
from docopt import docopt
import os
import sqlite3
import sys

import wos_handler

INPUT_PATH = '<input_path>'
_vivo = '--vivo'
_pubmed = '--pubmed'
_wos = '--wos'
_folder = '--directory'

def bib2dict(bib_data):
    dict_data = {}
    row = 0
    col_names = set(y for x in bib_data.entries for y in x.keys())

    for x in bib_data.entries:
        row += 1
        dict_data[row] = {}

        for col_name in col_names:
            v = x.get(col_name, '')
            v = v.replace('\n', ' ')
            v = v.replace('\r', ' ')
            v = v.replace('\t', ' ')
            dict_data[row][col_name] = v.encode('utf-8').strip()

    return dict_data

def parse_dict(dict_data):
    pubs = []
    pub_auth = {}
    authors = []
    for line in dict_data.items():
        number, data = line
        author_str = data['author']
        people = author_str.split(" and ")

        pubs.append((data['doi'], data['issn'], data['title'], data['year'], data['type']))
        pub_auth[data['doi']] = people
        for author in people:
            if author not in authors:
                authors.append(author)

    return (pubs, pub_auth, authors)

def main(args):
    #TODO: add log to keep track of finished files
    files = []
    if args[_folder]:
        roots, dirs, filenames = os.walk(args[INPUT_PATH])
        for file in filenames:
            files.append(os.path.join(args[INPUT_PATH], file))
    else:
        files.append(args[INPUT_PATH])

    for file in files:
        if args[_vivo]:
            #stuff
            pass

        if args[_pubmed]:
            #stuff
            pass

        if args[_wos]:
            handler = wos_handler
            bib_str = ""
            with open (args[INPUT_PATH], 'r') as bib:
                for line in bib:
                    bib_str += line
            bib_data = loads(bib_str)
            dict_data = bib2dict(bib_data)
            pubs, pub_auth, authors = parse_dict(dict_data)

        conn = sqlite3.connect('vivo.db')
        c = conn.cursor()
        handler.prepare_tables(c)

        handler.add_pubs(c, pubs)
        handler.add_authors(c, authors)
        handler.add_pub_auth(c, pub_auth)
        conn.commit()

if __name__ == '__main__':
    args = docopt(docstr)
    main(args)
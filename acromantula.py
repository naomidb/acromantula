docstr = """
Acromanutla
Usage:
    acromantula.py (-h | --help)
    acromantula.py [-wd] (<input_path>)
    acromantula.py [-pd] (<input_path>)
    acromantula.py [-vd] (<input_path>)
    acromantula.py -a (-w | -v | -p)


Options:
  -h --help                     Show this message and exit
  -w --wos                      Input file is bibtex from Web of Science site
                       
  -p --pubmed                   Input file is __ from pubmed
  -v --vivo                     Input file is csv from vivo
  -a --api
  -d --directory                Input is a directory of files

Instructions:
    You must always include a flag for either wos, vivo, or pubmed. The --api flag signifies using the api for whichever service you are accessing. Otherwise, you must include an input file. The file should be a bibtex for wos, a csv for vivo, or a __ for pubmed.

"""


#TODO: add config or argument for where to save database

from bibtexparser import loads
import csv
from docopt import docopt
import os
import sqlite3
import sys
import xml.etree.cElementTree as ET
import yaml

from owlspider import WOSnnection
import wos_handler
import vivo_handler

INPUT_PATH = '<input_path>'
_vivo = '--vivo'
_pubmed = '--pubmed'
_wos = '--wos'
_api = '--api'
_folder = '--directory'

class Foo(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        try:
            self.data[key] = self.data[key].replace('\xc2\x80\xc2\x93', '')
            self.data[key] = self.data[key].replace("\xc3\xa2\xc2\x80\xc2\x98", "'")
            self.data[key] = self.data[key].replace("\xc3\xa2\xc2\x80\xc2\x99", "'")
            self.data[key] = self.data[key].replace('\xc3\x83\xc2\xaf', 'i')
            self.data[key] = self.data[key].replace('\xc2\xa0', ' ')
            self.data[key] = self.data[key].replace('\xc2\xae', '')
            self.data[key] = self.data[key].replace('\xc3\xa2', '-')
            self.data[key] = self.data[key].replace('\xe2\x80\x93', '-')
            self.data[key] = self.data[key].replace('\xc3\x83\xc2\x83\xc3\x82\xc2\xb1', 'n')
            return self.data[key].encode('utf-8')
        except UnicodeDecodeError as e:
            import pdb
            pdb.set_trace()

def prep_vivo(csv_data):
    pubs = []
    pub_auth = {}
    authors = {}
    with open(csv_data, 'r') as table:
        # text = table.read().encode('utf-8')
        reader = csv.DictReader(table)
        for row in reader:
            row = Foo(row)
            pubs.append((row['nnum'], row['jname'], row['title'], row['year'], row['type']))

            if row['nnum'] not in pub_auth.keys():
                pub_auth[row['nnum']] = [row['author']]
            else:
                pub_auth[row['nnum']].append(row['author'])
            
            if row['author'] not in authors.keys():
                authors[row['author']] = row ['authname']

    return (pubs, pub_auth, authors)           

def prep_wos(bib_data):
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

def prep_wos_api():
    try:
        with open('wos/wos_config.yaml', 'r') as config_file:
            config = yaml.load(config_file.read())
    except Exception, e:
        print("Error: Check config file")
        print(e)
        exit()

    credentials = config.get('b64_credentials')
    wosnnection = WOSnnection(credentials)

    query = raw_input()
    start = raw_input()
    end = raw_input()
    results = wosnnection.run_query(query, start, end)

    pubs = []
    pub_auth = {}
    authors = []
    for result in results:
        root = ET.fromstring(result)
        records = []
        for child in root.iter('records'):
            records.append(child)

        for record in records:
            title = doctype = authors = doi = issn = jname = year = ''

            titag = record.find('title')
            title = titag.find('value').text

            tytag = record.find('doctype')
            doctype = tytag.find('value').text

            autag = record.find('authors')
            people = autag.findall('value')
            authors = [person.text for person in people]

            #DOI, ISSN
            others = record.findall('other')
            for other in others:
                if other.find('label'),text == 'Identifier.Doi':
                    doi = other.find('value').text
                if other.find('label'),text == 'Identifier.Issn':
                    issn = other.find('value').text
            pub_auth[doi] = authors

            #Pub year, Journal
            sources = record.findall('sources')
            for source in sources:
                if source.find('label'),text == 'Published.BiblioYear':
                    year = source.find('value').text
                if source.find('label'),text == 'SourceTitle':
                    jname = source.find('value').text
            pubs.append((doi, issn, title, year, doctype))

    return (pubs, pub_auth, authors)

def insert(handler, pubs, authors, pub_auth):
    conn = sqlite3.connect('vivo.db')
    c = conn.cursor()
    handler.prepare_tables(c)

    handler.add_pubs(c, pubs)
    handler.add_authors(c, authors)
    handler.add_pub_auth(c, pub_auth)
    conn.commit()

def main(args):
    if args[_api]:
        if args[_vivo]:
            handler = vivo_handler
            pass

        if args[_pubmed]:
            #stuff
            pass

        if args[_wos]:
            handler = wos_handler
            pubs, authors, pub_auth = prep_wos_api()
        insert(handler, pubs, authors, pub_auth)

    else:
        #TODO: add log to keep track of finished files
        files = []
        if args[_folder]:
            for roots, dirs, filenames in os.walk(args[INPUT_PATH]):
                for file in filenames:
                    files.append(os.path.join(args[INPUT_PATH], file))
        else:
            files.append(args[INPUT_PATH])

        for file in files:
            if args[_vivo]:
                handler = vivo_handler
                pubs, pub_auth, authors = prep_vivo(file)

            if args[_pubmed]:
                #stuff
                pass

            if args[_wos]:
                handler = wos_handler
                bib_str = ""
                with open (file, 'r') as bib:
                    for line in bib:
                        bib_str += line
                bib_data = loads(bib_str)
                pubs, pub_auth, authors = prep_wos(bib_data)

            insert(handler, pubs, authors, pub_auth)

if __name__ == '__main__':
    args = docopt(docstr)
    main(args)
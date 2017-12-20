import csv
import sqlite3
from time import localtime, strftime
import xml.etree.cElementTree as ET

from owlspider import WOSnnection

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
    journals = {}
    pub_journ = {}
    for line in dict_data.items():
        number, data = line
        author_str = data['author']
        people = author_str.split(" and ")

        try:
            volume = data['volume']
        except KeyError as e:
            volume = ''
        try:
            issue = data['issue']
        except KeyError as e:
            issue = ''

        wosid = data['unique-id'].replace('ISI', 'WOS')
        pubs.append((data['doi'], data['title'], data['year'], volume, issue, data['pages'], data['type'], wosid))
        pub_auth[wosid] = people
        for author in people:
            if author not in authors:
                authors.append(author)
        if data['issn'] not in journals.keys():
            journals[data['issn']] = data['journal'].replace('&amp;', '&')
        pub_journ[wosid] = data['issn']

    return (pubs, pub_auth, authors, journals, pub_journ)

def get_data(credentials, query, start, end):
    wosnnection = WOSnnection(credentials)
    results = wosnnection.run_query(query, start, end)

    return results

def prep_wos_api(results):
    pubs = []
    pub_auth = {}    
    journals = {}
    pub_journ = {}
    authors = []
    for result in results:
        root = ET.fromstring(result)
        records = []
        for child in root.iter('records'):
            records.append(child)

        for record in records:
            doi = issn = jname = year = volume = issue = page = ''
            
            titag = record.find('title')
            title = titag.find('value').text

            tytag = record.find('doctype')
            doctype = tytag.find('value').text

            wosid = record.find('uid').text

            autag = record.find('authors')
            people = autag.findall('value')
            crowd = [person.text for person in people]
            authors.extend(crowd)

            #DOI, ISSN
            others = record.findall('other')
            for other in others:
                if other.find('label').text == 'Identifier.Doi':
                    doi = other.find('value').text
                if other.find('label').text == 'Identifier.Issn':
                    issn = other.find('value').text            

            #Pub year, Journal
            sources = record.findall('source')
            for source in sources:
                if source.find('label').text == 'Published.BiblioYear':
                    year = source.find('value').text
                if source.find('label').text == 'SourceTitle':
                    jname = source.find('value').text.replace('&amp;', '&')
                if source.find('label').text == 'Volume':
                    volume = source.find('value').text
                if source.find('label').text == 'Issue':
                    issue = source.find('value').text
                if source.find('label').text == 'Pages':
                    pages = source.find('value').text

            pubs.append((doi, title, year, volume, issue, pages, doctype, wosid))
            pub_auth[wosid] = crowd
            journals[issn] = jname
            pub_journ[wosid] = issn

    return (pubs, pub_auth, authors, journals, pub_journ)

def prepare_tables(c):
    print("Make tables")
    c.execute('''create table if not exists wos_pubs
                    (doi text, title text, year text, volume text, issue text, pages text, type text, wosid text unique, created_dt text, modified_dt text, modified_by text)''')

    c.execute('''create table if not exists wos_authors
                    (author text unique, created_dt text, modified_dt text, modified_by text)''')

    c.execute('''create table if not exists wos_journals
                    (issn text unique, title text, created_dt text, modified_dt text, modified_by text)''')

    c.execute('''create table if not exists wos_pub_auth
                    (wosid text, auth text, created_dt text, modified_dt text, modified_by text, unique (wosid, auth))''')

    c.execute('''create table if not exists wos_pub_journ
                    (wosid text, issn text, created_dt text, modified_dt text, modified_by text, unique (wosid, issn))''')

def add_pubs(c, pubs, source):
    print("Adding publications")
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for pub in pubs:
        try:
            dataset = pub + (timestamp, timestamp, source)
            c.execute('INSERT INTO wos_pubs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (dataset))
        except sqlite3.IntegrityError as e:
            pass

def add_authors(c, authors, source):
    print("Adding authors")
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for auth in authors:
        try:
            c.execute('INSERT INTO wos_authors VALUES(?, ?, ?, ?)', (auth, timestamp, timestamp, source))
        except sqlite3.IntegrityError as e:
            pass

def add_journals(c, journals, source):
    print("Adding journals")
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for issn, title in journals.items():
        try:
            c.execute('INSERT INTO wos_journals VALUES (?, ?, ?, ?, ?)', (issn, title, timestamp, timestamp, source))
        except sqlite3.IntegrityError as e:
            pass

def add_pub_auth(c, pub_auth, source):
    print("Add publication-author linkages")
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for wosid, auth_list in pub_auth.items():
        for auth in auth_list:
            try:
                c.execute('INSERT INTO wos_pub_auth VALUES(?, ?, ?, ?, ?)', (wosid, auth, timestamp, timestamp, source))
            except sqlite3.IntegrityError as e:
                pass

def add_pub_journ(c, pub_journ, source):
    print("Adding publication-journal linkages")
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for wosid, issn in pub_journ.items():
        try:
            c.execute('INSERT INTO wos_pub_journ VALUES(?, ?, ?, ?, ?)', (wosid, issn, timestamp, timestamp, source))
        except sqlite3.IntegrityError as e:
            pass
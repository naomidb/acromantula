import sqlite3 #probably don't need this?
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

def prep_wos_api(credentials):
    wosnnection = WOSnnection(credentials)

    query = raw_input('Enter query: ')
    start = raw_input('Enter start date: ')
    end = raw_input('Enter end date: ')
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

def prepare_tables(c):
    c.execute('''create table if not exists wos_pubs
                    ("doi" text, "issn" text, "title" text, "year" text, "type" text)''')

    c.execute('''create table if not exists wos_authors
                    (author text unique)''')

    c.execute('''create table if not exists wos_pub_auth
                    (doi text, auth text)''')

def add_pubs(c, pubs):
    for pub in pubs:
        try:
            c.execute('INSERT INTO wos_pubs VALUES (?, ?, ?, ?, ?)', pub)
        except sqlite3.IntegrityError as e:
            pass

def add_authors(c, authors):
    for auth in authors:
        try:
            c.execute('INSERT INTO wos_authors VALUES(?)', [auth])
        except sqlite3.IntegrityError as e:
            pass

def add_pub_auth(c, pub_auth):
    for doi, auth_list in pub_auth.items():
        for auth in auth_list:
            try:
                c.execute('INSERT INTO wos_pub_auth VALUES(?, ?)', (doi, auth))
            except sqlite3.IntegrityError as e:
                pass
import csv
import sqlite3

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

def prepare_tables(c):
    c.execute('''create table if not exists vivo_pubs
                    ("n_num" text primary key, "issn" text, "title" text, "year" text, "type" text)''')

    c.execute('''create table if not exists vivo_authors
                    (author text unique, author_name text)''')

    c.execute('''create table if not exists vivo_pub_auth
                    (n_num text, auth text)''')

def add_pubs(c, pubs):
    for pub in pubs:
        try:
            c.execute('INSERT INTO vivo_pubs VALUES (?, ?, ?, ?, ?)', pub)
        except sqlite3.IntegrityError as e:
            pass

def add_authors(c, authors):
    for auth_n, name in authors.items():
        try:
            c.execute('INSERT INTO vivo_authors VALUES(?, ?)', (auth_n, name))
        except sqlite3.IntegrityError as e:
            pass

def add_pub_auth(c, pub_auth):
    for nnum, auth_list in pub_auth.items():
        for auth in auth_list:
            try:
                c.execute('INSERT INTO vivo_pub_auth VALUES(?, ?)', (nnum, auth))
            except sqlite3.IntegrityError as e:
                pass
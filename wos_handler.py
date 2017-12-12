import sqlite3

def prepare_tables(c):
    c.execute('''create table if not exists wos_pubs
                    ("doi" text primary key, "issn" text, "title" text, "year" text, "type" text)''')

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
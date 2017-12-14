import sqlite3

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
import sqlite3
import xml.etree.cElementTree as ET
import yaml

import wos_handler

def get_credentials():
    try:
        with open('wos/wos_config.yaml', 'r') as config_file:
            config = yaml.load(config_file.read())
    except Exception, e:
        print("Error: Check config file")
        print(e)
        exit()

    credentials = config.get('b64_credentials')
    return credentials

def insert(pubs, pub_auth, authors, journals, pub_journ):
    conn = sqlite3.connect('epd.db')
    c = conn.cursor()
    wos_handler.prepare_tables(c)

    wos_handler.add_pubs(c, pubs, 'wos_aggregator')
    wos_handler.add_authors(c, authors)
    wos_handler.add_journals(c, journals, 'wos_aggregator')
    wos_handler.add_pub_auth(c, pub_auth, 'wos_aggregator')
    wos_handler.add_pub_journ(c, pub_journ, 'wos_aggregator')
    conn.commit()

def main():
    credentials = get_credentials()

    results = wos_handler.get_data(credentials, 'AD=(University Florida OR Univ Florida OR UFL OR UF)', '2016-12-28', '2016-12-31')
    pubs, pub_auth, authors, journals, pub_journ = wos_handler.prep_wos_api(results)

    insert(pubs, pub_auth, authors, journals, pub_journ)

    for result in results:
        root = ET.fromstring(result)
        records = []
        for child in root.iter('records'):
            wosid = child.find('uid').text[4:]
            filename = 'data/wos_data/' + wosid + '.xml'
            branch = ET.tostring(child, encoding='utf-8', method='xml')
            sapling = branch.replace('>', '>\n')
            with open(filename, 'w') as output:
                output.write(sapling)

if __name__ == '__main__':
    main()
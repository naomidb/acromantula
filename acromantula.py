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
from docopt import docopt
import os
import sqlite3
import sys
import yaml

import wos_handler
import vivo_handler

INPUT_PATH = '<input_path>'
_vivo = '--vivo'
_pubmed = '--pubmed'
_wos = '--wos'
_api = '--api'
_folder = '--directory'         

def insert(handler, pubs, authors, pub_auth, journals, pub_journ):
    conn = sqlite3.connect('testing.db')
    c = conn.cursor()
    handler.prepare_tables(c)

    handler.add_pubs(c, pubs, 'acromantula')
    handler.add_authors(c, authors)
    handler.add_pub_auth(c, pub_auth)
    conn.commit()

def main(args):
    #Using api
    if args[_api]:
        if args[_vivo]:
            handler = vivo_handler
            pass

        if args[_pubmed]:
            #stuff
            pass

        if args[_wos]:
            handler = wos_handler
            try:
                with open('api_config.yaml', 'r') as config_file:
                    config = yaml.load(config_file.read())
            except Exception, e:
                print("Error: Check config file")
                print(e)
                exit()

            credentials = config.get('b64_credentials')
            query = raw_input('Enter query: ')
            start = raw_input('Enter start date: ')
            end = raw_input('Enter end date: ')
            results = handler.get_data(credentials, query, start, end)
            pubs, authors, pub_auth, journals, pub_journ = handler.prep_wos_api(results)
        
        insert(handler, pubs, authors, pub_auth, journals, pub_jour)

    #Using input files
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
                pubs, pub_auth, authors = handler.prep_vivo(file)

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
                pubs, pub_auth, authors = handler.prep_wos(bib_data)

            insert(handler, pubs, authors, pub_auth)

if __name__ == '__main__':
    args = docopt(docstr)
    main(args)
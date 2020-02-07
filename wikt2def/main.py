import sys
import argparse
from urllib.request import urlretrieve
from os import path
from subprocess import call
import external.config as config
from external.wiktionary import Wiktionary


parser = argparse.ArgumentParser(description = "")
parser.add_argument("-d", "--download", action = "store_true", help = "download data")
parser.add_argument("-x", "--definitions", action = "store_true", help = "extract definitions")
parser.add_argument("-w", "--wikicodes", required = True, nargs = "+", help = "languages")


args = parser.parse_args()

def download_wiktionaries(wc_set):
    to_download = filter(lambda c: c.wc in wc_set, config.configs)
    for cfg in to_download:
        urlretrieve(cfg.dump_url, cfg.bz2_path)
        wiki_textify_path = path.join(config.base_dir, 'articles.py')
        call(['bzcat {0} | python3 {1} > {2}'.format(
            cfg.bz2_path, wiki_textify_path, cfg.dump_path)], shell=True)

def extract_translations(wc_set):
    to_parse = filter(lambda c: c.wc in wc_set, config.configs)
    for cfg in to_parse:
        wikt = Wiktionary(cfg)
        wikt.parse_articles()

def get_wikicodes(wikicodes):
    if len(wikicodes) == 1:
        try:
            with open(wikicodes[0]) as f:
                wc_set = set([l.strip() for l in f])
        except FileNotFoundError:
            wc_set = set(wikicodes) # idk how to do this
    else:
        wc_set = set(wikicodes)

    return wc_set

def main(download, definitions, wikicodes):
    wc_set = get_wikicodes(wikicodes)
    # print(wc_set)
    if download:
        download_wiktionaries(wc_set)
    if definitions:
        #extract_definitions(wc_set) 
        extract_translations(wc_set)  
 
if __name__ == '__main__':
    main(args.download, args.definitions, args.wikicodes)

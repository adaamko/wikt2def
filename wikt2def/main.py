import sys
import argparse
from urllib.request import urlretrieve
from os import path
from subprocess import call
import config


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

def print_definition(word, pos, definition, category, def_f):
    if pos == "":
        pos = "-"
    pipe_idx = pos.find("|")
    if -1 < pipe_idx:
        pos = pos[:pipe_idx]
    
    categories = "\t".join(category)
    if categories == "":
        categories = "-"
    
    if len(definition) == 0:
        definition = ["-"]
    
    for d in definition:
        print("{}\t{}\t{}\t{}".format(word, pos, d, categories), file=def_f)

def extract_definitions(wc_set):
    to_parse = filter(lambda c: c.wc in wc_set, config.configs)
    word = ""
    pos = ""
    definition = []
    category = []
    for cfg in to_parse:
        with open(cfg.dump_path) as dump_f, open(cfg.def_path, "w") as def_f:
            for line in dump_f:
                if line.startswith("%%#PAGE"):
                    print_definition(word, pos, definition, category, def_f)
                    word = ""
                    pos = ""
                    definition = []
                    category = []
                    word = line[8:-1]
                if line.startswith("#"):
                    definition.append(line[1:-1])
                if line.startswith("[[Kategória"):
                    category.append(line[12:-3])
                if line.startswith("{{" + cfg.wc) and pos == "":
                    pos = line[5:-3]
            print_definition(word, pos, definition, category, def_f)


def main(download, definitions, wikicodes):
    wc_set = get_wikicodes(wikicodes)
    # print(wc_set)
    if download:
        download_wiktionaries(wc_set)
    if definitions:
        extract_definitions(wc_set)   
 
if __name__ == '__main__':
    main(args.download, args.definitions, args.wikicodes)

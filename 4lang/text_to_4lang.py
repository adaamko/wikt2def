import json
import logging
import os
import re
import sys

from dep_to_4lang import DepTo4lang

__LOGLEVEL__ = 'INFO'
__MACHINE_LOGLEVEL__ = 'INFO'


class TextTo4lang():
    square_regex = re.compile("\[.*?\]")
    
    def __init__(self, lang):
        self.lang = lang
        self.parser_wrapper = StanfordParser(self.lang)
        self.dep_to_4lang = DepTo4lang()

    def preprocess_text(text):
        t = text.strip()
        t = TextTo4lang.square_regex.sub('', t)
        t = t.replace(u"=", u"_eq_")
        t = t.replace(u"\xc2\xa0", u" ")
        t = t.replace(u"\xa0", u" ")
        t = t.strip()
        return t

def main():
    logging.basicConfig(
        level=__LOGLEVEL__,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    pass


if __name__ == "__main__":
    main()

"""
Adapted from https://github.com/juditacs/wikt2dict/blob/master/wikt2dict/article_parsers.py

Copyright (C) Judit Ács

Permissions of this copyleft license are conditioned on making available 
complete source code of licensed works and modifications under the same 
license or the GNU GPLv3. Copyright and license notices must be preserved. 
Contributors provide an express grant of patent rights. 
However, a larger work using the licensed work through interfaces provided 
by the licensed work may be distributed under different terms and without 
source code for the larger work.
"""

from .article import ArticleParser
import re


class SectionAndArticleParser(ArticleParser):
    """
    Class for parsing Wiktionaries that have translation tables
    in foreign articles too and section-level parsing is required.
    e.g. dewiktionary has a translation section in the article
    about the English word dog. Therefore, we need to recognize
    the language of the title word (dog) and then parse the
    translation table.
    """

    def extract_definitions(self, title, text):
        definitions = []
        group = None
        section = None
        for line in text.split("\n"):
            lan_re = self.cfg.lan_re.match(line)
            if lan_re:
                group = lan_re.group()
            get_section = self.cfg.section.match(line)
            if get_section:
                if get_section.group(1):
                    section = get_section.group(1)
                elif get_section.group(2):
                    section = None
            def_re = self.cfg.def_re.match(line)

            if def_re and group and section:
                definition = def_re.group()
                beg_match = self.cfg.beg_re.match(definition)
                com_match = self.cfg.com_re.findall(definition)
                if com_match:
                    last_match = com_match[-1]
                    split_def = definition.split(last_match)
                    if len(split_def) > 1 and split_def[1].strip():
                        definitions.append((title, group, self.trim_translation(split_def[1])))
                else:
                    split_def = definition.split(beg_match.group())
                    definitions.append((title, group, self.trim_translation(split_def[1])))

        return definitions

    def skip_word(self, word):
        if self.cfg.skip_translation_re and self.cfg.skip_translation_re.search(word):
            return True
        if '\n' in word:
            return True
        return False


class LangnamesArticleParser(ArticleParser):
    """
    Class for parsing Wiktionaries that use simple lists for translations
    instead of templates """

    def __init__(self, wikt_cfg, parser_cfg, filter_langs=None):
        ArticleParser.__init__(self, wikt_cfg, parser_cfg, filter_langs)
        self.read_langname_mapping()

    def read_langname_mapping(self):
        self.mapping = dict()
        if self.cfg.langnames:
            f = open(self.cfg.langnames)
            for l in f:
                fields = l.strip().decode('utf8').split('\t')
                for langname in fields[1:]:
                    self.mapping[langname] = fields[0]
                    self.mapping[langname.title()] = fields[0]
                    self.mapping[langname.lower()] = fields[0]
            f.close()
        else:
            self.mapping = dict([(wc, wc) for wc in self.wikt_cfg.wikicodes])

    def extract_translations(self, title, text):
        translations = list()
        for tr in self.cfg.translation_line_re.finditer(text):
            if self.skip_translation_line(tr.group(0)):
                continue
            langname = tr.group(self.cfg.language_name_field).lower()
            if not langname in self.mapping:
                continue
            wc = self.mapping[langname]
            entities = self.get_entities(tr.group(self.cfg.translation_field))
            for entity in entities:
                entity_clear = self.trim_translation(entity)
                if entity_clear:
                    translations.append((wc, entity_clear))
        return set(translations)

    def trim_translation(self, word):
        return word.replace('\n', ' ').strip()

    def get_entities(self, trans_field):
        trimmed = self.cfg.bracket_re.sub('', trans_field)
        entities = list()
        for e in self.cfg.delimiter_re.split(trimmed):
            for m in self.cfg.translation_re.finditer(e):
                word = m.group(1)
                if self.skip_entity(word):
                    continue
                entities.append(word)
        return set(entities)

    def skip_entity(self, entity):
        if self.cfg.skip_translation_re.search(entity):
            return True
        if self.cfg.junk_re and self.cfg.junk_re.search(entity):
            return True
        return False


class DefaultArticleParser(ArticleParser):

    def extract_definitions(self, title, text):
        definitions = []
        group = None
        for line in text.split("\n"):

            lan_re = self.cfg.lan_re.match(line)
            if lan_re:
                group = lan_re.group()
            def_re = self.cfg.def_re.match(line)

            if def_re and group:
                definition = def_re.group()
                beg_match = self.cfg.beg_re.match(definition)
                com_match = self.cfg.com_re.findall(definition)
                if com_match:
                    last_match = com_match[-1]
                    split_def = definition.split(last_match)
                    if len(split_def) > 1 and split_def[1].strip():
                        definitions.append((title, group, self.trim_translation(split_def[1])))
                    else:
                        if len(com_match) > 1:
                            split_def = definition.split(com_match[-2])
                            if len(split_def) > 1:
                                definitions.append((title, group, self.trim_translation(split_def[1])))
                else:
                    split_def = definition.split(beg_match.group())
                    definitions.append((title, group, self.trim_translation(split_def[1])))

        return definitions

    def skip_word(self, word):
        if self.cfg.skip_translation_re and self.cfg.skip_translation_re.search(word):
            return True
        if '\n' in word:
            return True
        return False

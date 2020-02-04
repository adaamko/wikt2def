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

    def __init__(self, wikt_cfg, parser_cfg, filter_langs=None):
        ArticleParser.__init__(self, wikt_cfg, parser_cfg, filter_langs)
        self.read_section_langmap()

    def read_section_langmap(self):
        """
        The language of a section is determined based on its header.
        The header may or may not use language names.
        If a language name map is specified, then each section header
        will be looked up in that map.
        Otherwise wikicodes are used.
        """
        self.section_langmap = dict()
        if self.cfg.section_langmap:
            f = open(self.cfg.section_langmap)
            for l in f:
                fields = l.strip().decode('utf8').split('\t')
                for langname in fields[1:]:
                    self.section_langmap[langname] = fields[0]
                    self.section_langmap[langname.title()] = fields[0]
            f.close()
        else:
            self.section_langmap = dict([(wc, wc) for wc in self.wikt_cfg.wikicodes])

    def extract_translations(self, title, text):
        translations = list()
        for section_lang, section in self.get_sections(text):
            for parser in self.wikt_cfg.section_parsers:
                pairs = parser.extract_translations(title, section)
                for p in pairs:
                    if self.wikt_cfg.allow_synonyms is False and p[0] == section_lang:
                        continue
                    translations.extend([(section_lang, title, p[0], p[1])
                                         for p in pairs])
        return set(translations)

    def get_sections(self, text):
        section_titles_i = list()
        lines = text.split('\n')
        for i, line in enumerate(lines):
            m = self.cfg.section_re.search(line)
            if m:
                lang = m.group(self.cfg.section_langfield)
                section_titles_i.append((i, lang))
        if not section_titles_i:
            return
        for i, (ind, lang) in enumerate(section_titles_i[:-1]):
            if lang in self.section_langmap:
                yield self.section_langmap[lang], \
                    '\n'.join(lines[ind:section_titles_i[i + 1][0]])
        last_lang = section_titles_i[-1][1]
        if last_lang in self.section_langmap:
            yield self.section_langmap[last_lang], '\n'.join(lines[section_titles_i[-1][0]:])


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

    def extract_translations(self, title, text):
        translations = list()
        definitions = []
        group = None
        comments = re.compile(r'\{\{.*\}\}')
        beginning = re.compile(r'^\# ')
        for line in text.split("\n"):
            lan_re = self.cfg.lan_re.match(line)
            if lan_re:
                group = lan_re.group()
            def_re = self.cfg.def_re.match(line)
            if def_re:
                definition = def_re.group()
                beg_match = beginning.match(definition)
                com_match = comments.findall(definition)
                if com_match:
                    last_match = com_match[-1]
                    split_def = definition.split(last_match)
                    if len(split_def) > 1 and split_def[1].strip():
                        definitions.append((title, group, self.trim_translation(split_def[1])))
                else:
                    split_def = definition.split(beg_match.group())
                    definitions.append((title, group, self.trim_translation(split_def[1])))

        """
        for tr in self.cfg.lan_re.finditer(text):
            print(tr)
        for tr in self.cfg.def_re.finditer(text):
            defin = tr.group()
            if not defin or not defin.strip():
                continue
            print(defin)
        """

        for tr in self.cfg.trad_re.finditer(text):
            wc = tr.group(self.cfg.wc_field)
            if not wc or not wc.strip() or not wc in self.wikt_cfg.wikicodes:
                continue
            word = tr.group(self.cfg.word_field)
            if not word or not word.strip():
                continue
            word = word.strip()
            if self.skip_word(word):
                continue
            translations.append((wc, word))
        print(definitions)
        return set(translations)

    def extract_definitions(self, title, text):
        definitions = []
        group = None
        comments = re.compile(r'\{\{.*\}\}')
        beginning = re.compile(r'^\# ')
        for line in text.split("\n"):
            lan_re = self.cfg.lan_re.match(line)
            if lan_re:
                group = lan_re.group()
            def_re = self.cfg.def_re.match(line)
            if def_re:
                definition = def_re.group()
                beg_match = beginning.match(definition)
                com_match = comments.findall(definition)
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

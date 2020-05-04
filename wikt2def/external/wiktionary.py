import os


class Wiktionary(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.init_parsers()
        self.triplets = list()
        self.synonyms = list()

    def init_parsers(self):
        self.parsers = list()
        for parser_cl, parser_cfg in self.cfg.parsers:
            self.parsers.append(parser_cl(self.cfg, parser_cfg))

    def parse_articles(self, write_immediately=False):
        self.syn_file = open(os.path.join(os.path.dirname(self.cfg.output_path), "synonyms"), 'w')
        with open(self.cfg.output_path, 'w') as self.outf:
            i = 0
            for title, text in self.read_dump():
                # if i > 1000:
                #     break
                i += 1
                triplets = self.extract_definitions(title, text)
                synonym = self.extract_synonyms(title, text)
                if synonym:
                    self.synonyms += synonym
                if triplets:
                    self.store_translations(triplets)
            if not write_immediately:
                self.write_all_pairs()
                for syn in self.synonyms:
                    self.syn_file.write("{}\t{}\n".format(syn[0], syn[1]))

    def extract_translations(self, title, text):
        if self.skip_article(title, text):
            return
        pairs = list()
        for parser in self.parsers:
            for p in parser.extract_translations(title, text):
                if len(p) == 2:
                    pair = ((self.cfg.wc, title, p[0], p[1]), tuple(parser.cfg.features))
                elif len(p) == 4:
                    pair = (p, tuple(parser.cfg.features))
                else:
                    raise Exception('Invalid pair {0}'.format(p))
                pairs.append(pair)
        return set(pairs)

    def extract_definitions(self, title, text):
        if self.skip_article(title, text):
            return
        triplets = list()
        for parser in self.parsers:
            for t in parser.extract_definitions(title, text):
                triplets.append(t)
        return triplets

    def extract_synonyms(self, title, text):
        if self.skip_article(title, text):
            return
        pairs = list()
        for parser in self.parsers:
            for t in parser.extract_synonyms(title, text):
                pairs.append(t)
        return pairs

    def skip_article(self, title, text):
        if not title.strip() or not text.strip():
            return True
        if ':' in title:  # skipping namespaced articles
            return True
        return False

    def write_one_article_translations(self, pairs):
        for pair in pairs:
            if self.cfg.verbose_output is True:
                self.outf.write('\t'.join(pair[0]).encode('utf8') + '\n')
            else:
                self.outf.write('\t'.join(pair[0:4]).encode('utf8') + '\n')

    def store_translations(self, triplets):
        for triplet in triplets:
            self.triplets.append(triplet)

    def write_all_pairs(self):
        for pair in self.triplets:
            self.outf.write('\t'.join(pair) + '\n')

    def read_dump(self):
        with open(self.cfg.dump_path) as f:
            title = u''
            article = u''
            page_sep = '%%#PAGE'
            for l in f:
                if l.startswith(page_sep):
                    if title and article:
                        yield title, article
                    title = l.split(page_sep)[-1].strip()
                    article = u''
                else:
                    article += l
            yield title, article

class Wiktionary(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.init_parsers()
        self.triplets = list()

    def init_parsers(self):
        self.parsers = list()
        for parser_cl, parser_cfg in self.cfg.parsers:
            self.parsers.append(parser_cl(self.cfg, parser_cfg))

    def parse_articles(self, write_immediately=False):
        with open(self.cfg.output_path, 'w') as self.outf:
            i = 0
            for title, text in self.read_dump():
                # if i > 1000:
                #     break
                i += 1
                triplets = self.extract_definitions(title, text)
                if triplets:
                    self.store_translations(triplets)
            if write_immediately is False:
                self.write_all_pairs()

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
        return set(triplets)

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
        for pair in sorted(self.triplets):
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
import os


REPLACE_MAP = {
    ":": "COLON",
    ",": "COMMA",
    ".": "PERIOD",
    ";": "SEMICOLON",
    "-": "HYPHEN",
    "_": "DASH",
    "[": "LSB",
    "]": "RSB",
    "(": "LRB",
    ")": "RRB",
    "{": "LCB",
    "}": "RCB",
    "!": "EXC",
    "?": "QUE",
    "'": "SQ",
    '"': "DQ",
    "/": "PER",
    "\\": "BSL",
    "#": "HASHTAG",
    "%": "PERCENT",
    "&": "ET",
    "@": "AT",
    "$": "DOLLAR",
    "*": "ASTERISK",
    "^": "CAP",
    "`": "IQ",
    "+": "PLUS",
    "|": "PIPE",
    "~": "TILDE",
    "<": "LESS",
    ">": "MORE",
    "=": "EQ"
}


class UdToFourlangGrammar():
    def __init__(self):
        super().__init__()

    def generate_grammar(self, root_i, word_index, og):
        return

    def generate_terminals(self, root_i, word_index, og):
        return


class UdToFourlang():
    """
    Generates IRTG grammar from ud parse of a text
    """

    def __init__(self):
        super().__init__()
        self.grammar = UdToFourlangGrammar()

    def print_input_header(self, sen, f):
        top_lines = [
            "# IRTG unannotated corpus file, v1.0",
            "# interpretation ud: de.up.ling.irtg.algebra.graph.GraphAlgebra"]
        words = " ".join([w.text for w in sen.words])
        lemmas = " ".join([w.lemma for w in sen.words])
        pos = " ".join([w.upos for w in sen.words])
        s, e = ("#", "")
        lines = top_lines + [
            "",
            f"{s} Words: {words} {e}",
            f"{s} Lemmas: {lemmas} {e}",
            f"{s} POS: {pos} {e}",
            ""]
        f.write('\n'.join(lines))

    def print_grammar_header(self, sen, f):
        top_lines = [
            "interpretation ud: de.up.ling.irtg.algebra.graph.GraphAlgebra",
            "interpretation fourlang: de.up.ling.irtg.algebra.graph.GraphAlgebra"
        ]
        words = " ".join([w.text for w in sen.words])
        lemmas = " ".join([w.lemma for w in sen.words])
        pos = " ".join([w.upos for w in sen.words])
        s, e = ("/*", "*/")
        lines = top_lines + [
            "",
            f"{s} Words: {words} {e}",
            f"{s} Lemmas: {lemmas} {e}",
            f"{s} POS: {pos} {e}",
            ""]
        f.write('\n'.join(lines))

    def generate_rules(self, sen, root_i, word_index, og):
        root_pos = word_index[root_i][2]
        og.write(f"S! -> ROOT({root_pos})\n")
        og.write("[ud] ?1\n")
        og.write("[fl] ?1\n\n")
        self.grammar.generate_grammar(root_i, word_index, og)
        og.write("/* terminal rules */\n\n")

        self.grammar.generate_terminals(root_i, word_index, og)

    def make_graph_string(self, i, word_index):
        _, lemma, pos, children = word_index[i]
        graph_string = "({0} / {0}".format(lemma)
        for dep, j in children:
            graph_string += ' :{0} '.format(dep.replace(':', '_'))
            graph_string += self.make_graph_string(j, word_index)
        graph_string += ")"
        return graph_string

    def preprocess_word_for_alto(self, word):
        out = word
        for a, b in REPLACE_MAP.items():
            out = out.replace(a, b)
        if out[0].isdigit():
            out = "X" + out
        return out

    def get_word_index(self, sen):
        word_index = {
            int(word.index): (
                self.preprocess_word_for_alto(
                    word.text), self.preprocess_word_for_alto(word.lemma),
                word.upos, [])
            for word in sen.words}
        root_index = None
        for word in sen.words:
            if word.governor == 0:
                assert root_index is None, 'multiple root elements!'
                root_index = int(word.index)
            else:
                word_index[word.governor][-1].append((
                    word.dependency_relation.replace(':', '_').upper(),
                    int(word.index)))

        assert root_index, 'no root element!'
        return word_index, root_index

    def ud_to_irtg(self, doc):
        """
        Gets an ud parse as an input and generates an IRTG from it
        """
        base_fn = os.path.dirname(os.path.abspath(__file__))
        out = os.path.join(base_fn, "dep_to_4lang")
        with open(f"{out}.input", 'w') as of:
            for sen in doc.sentences:
                word_index, root_i = self.get_word_index(sen)
                self.print_input_header(sen, of)
                graph = self.make_graph_string(root_i, word_index)
                of.write(graph + "\n")
            of.write("(dummy_0 / dummy_0)\n")

        with open(f"{out}_{i}.irtg", 'w') as og:
            self.print_grammar_header(sen, og)
            self.generate_rules(sen, root_i, word_index, og)

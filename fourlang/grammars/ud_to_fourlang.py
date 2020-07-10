import os
from itertools import chain

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
        self.default_binary_rule = "?2"
        self.bin_fnc = {}
        self.relation_terms = set()

        def r_out(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :{fourlang_edge} (d1<dep1>))"), r_dep1(?2)))'

        def r_in(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(d1<dep1> :{fourlang_edge} (r<root>))"), r_dep1(?2)))'

        def r_relation(ud_edge, relation):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'[fourlang] f_dep1(merge(merge(?1,"({relation}<relation> / {relation} :1 (r<root>) :2 (d1<dep1>)))"), r_dep1(?2)))'

        def r_in_out(ud_edge, fourlang_out, fourlang_in):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :{fourlang_out} (d1<dep1> :{fourlang_in} (r<root>)))"), r_dep1(?2)))'

        def r_default_binary_rule(ud_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'?1'

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sorted_train_edges_mapped"), "r+") as f:
            for line in f:
                line = line.strip("\n")
                if line:
                    line = line.split("\t")
                    pos = line[0]
                    dep = line[2].replace(":", "_").upper()
                    cpos = line[1]
                    out_edge = None if line[4] == "-" else line[4]
                    in_edge = None if line[5] == "-" else line[5]

                    if in_edge and not out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_in(dep, in_edge)
                    elif not in_edge and out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_out(dep, out_edge)
                    elif in_edge and out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_in_out(
                            dep, in_edge, out_edge)
                    elif not in_edge and not out_edge and len(line) == 7:
                        self.relation_terms.add(line[6])
                        self.bin_fnc[(pos, dep, cpos)] = r_relation(
                            dep, line[6])
                    else:
                        self.bin_fnc[(pos, dep, cpos)
                                     ] = r_default_binary_rule(dep)

    def get_dependency_rules(self, pos, dep, cpos):
        return self.bin_fnc.get((pos, dep, cpos))

    def get_default_terminal(self, word):
        return f'"({word}<root> / {word})"', f'"({word}<root> / {word})"'

    def get_relation_terminal(self, word):
        return f'"({word}<relation> / {word})"', f'"({word}<relation> / {word})"'

    def generate_grammar(self, i, word_index, og):
        _, lemma, pos, children = word_index[i]
        #curr_terminal_lines = get_terminal_lines(lemma, pos)
        for dep, j in children:
            clemma, cpos = word_index[j][1:3]
            og.write(f"/* {lemma}_{pos} -{dep}-> {clemma}_{cpos} */\n\n")

            binary_fss = self.get_dependency_rules(pos, dep, cpos)

            binary_line = [
                "",
                f"{pos} -> {pos}_{cpos}_{dep}_{i}({pos}, {cpos})",
                f"[ud] {binary_fss[0]}",
                f"[fourlang] {binary_fss[1]}",
                ""
            ]

            og.write("\n".join(binary_line))

            self.generate_grammar(
                j, word_index, og)

    def generate_terminals(self, i, word_index, og):
        _, lemma, pos, children = word_index[i]
        terminal_fss = self.get_default_terminal(lemma)

        terminal_line = [
            "",
            f"{pos} -> {lemma}_{pos}_{i}",
            f"[ud] {terminal_fss[0]}",
            f'[fourlang] {terminal_fss[1]}',
            ""]

        og.write("\n".join(terminal_line))

        for dep, j in children:
            self.generate_terminals(j, word_index, og)

    def generate_relations(self, og):
        for i, relation in enumerate(self.relation_terms):
            terminal_fss = self.get_relation_terminal(relation)

            terminal_line = [
                "",
                f"{relation} -> {relation}_{i}",
                f"[ud] {terminal_fss[0]}",
                f'[fourlang] {terminal_fss[1]}',
                ""
            ]

            og.write("\n".join(terminal_line))


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
        og.write("[fourlang] f_root(f_relation(?1))\n\n")
        self.grammar.generate_grammar(root_i, word_index, og)
        og.write("/* terminal rules */\n\n")

        self.grammar.generate_terminals(root_i, word_index, og)

        og.write("/* relation terminal rules */\n\n")
        self.grammar.generate_relations(og)

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

        with open(f"{out}.irtg", 'w') as og:
            self.print_grammar_header(sen, og)
            self.generate_rules(sen, root_i, word_index, og)

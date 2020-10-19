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
        self.default_binary_rule = "?1"
        self.bin_fnc = {}
        self.relation_terms = set()

        def r_out(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :{fourlang_edge} (d1<dep1>))"), r_dep1(?2)))'

        def r_in(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(d1<dep1> :{fourlang_edge} (r<root>))"), r_dep1(?2)))'

        def r_relation(ud_edge, relation):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"({relation}<relation> / {relation} :1 (r<root>) :2 (d1<dep1>)))"), r_dep1(?2)))'

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

    def get_default_terminal(self, word, i):
        return f'"({i}<root> / {word})"', f'"({word}<root> / {word})"'

    def get_relation_terminal(self, word):
        return f'"({word}<relation> / {word})"', f'"({word}<relation> / {word})"'

    def generate_grammar(self, i, word_index, og, dependencies):
        _, lemma, pos, children = word_index[i]
        #curr_terminal_lines = get_terminal_lines(lemma, pos)
        for dep, j in children:
            clemma, cpos = word_index[j][1:3]
            og.write(f"/* {lemma}_{pos} -{dep}-> {clemma}_{cpos} */\n\n")

            binary_fss = self.get_dependency_rules(pos, dep, cpos)
            binary_line = [
                "",
                f"{pos} -> {pos}_{cpos}_{dep}_{i}({pos}, {cpos}) [{dependencies}]",
                f"[ud] {binary_fss[0]}",
                f"[fourlang] {binary_fss[1]}",
                ""
            ]

            og.write("\n".join(binary_line))

            self.generate_grammar(
                j, word_index, og, dependencies)

    def handle_conj(self, parent_pos, parent_dep, current_pos, children_pos, og, i):
        coordination = [
            "",
            f"{parent_pos} -> coordination_{i}(SUBGRAPHNODE, COORD)",
            f'[ud] f_dep1(merge(merge(?1,"(r<root> :{parent_dep} (d1<dep1>))"), r_dep1(?2)))',
            f'[fourlang] r_coord_root(merge(?1, ?2))',
            ""
        ]

        handle_coord = [
            "",
            f"COORD -> handle_coord_{i}(COORD, {children_pos})",
            f'[ud] f_dep1(merge(merge(?1,"(r<root> :CONJ (d1<dep1>))"), r_dep1(?2)))',
            f'[fourlang] f_dep1(merge(merge(?1,"(r<coord> :2 (d1<dep1>))"), r_dep1(?2)))',
            ""
        ]

        coord_to_pos = [
            "",
            f"COORD -> coord_to_{current_pos}{i}({current_pos})",
            f'[ud] ?1',
            f'[fourlang] f_dep1(merge("(r<coord> :2 (d1<dep1>))", r_dep1(?1)))',
            "",
            f"SUBGRAPHNODE -> subgraph_to_node{i}({parent_pos})",
            f"[ud] ?1",
            f'[fourlang] r_coord(?1)',
            ""
        ]
        og.write("\n".join(coordination))
        og.write("\n".join(handle_coord))
        og.write("\n".join(coord_to_pos))

    def handle_acl_relcl(self, parent_pos, current_pos, children_pos, og, i):
        acl_relcl = [
            "",
            f"{parent_pos} -> handle_acl_relcl{i}({parent_pos}, {current_pos}, {children_pos})",
            f'[ud] f_dep2(merge(merge(?1,"(r<root> :ACL_RELCL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :NSUBJ (d1<dep1>))"), r_dep1(?3))))))',
            f'[fourlang] f_dep1(merge(merge(?1,"(r<root> :0 (d1<dep1>))"), r_dep1(?2)))',
            ""
        ]

        og.write("\n".join(acl_relcl))

    def handle_obl_case(self, parent_pos, current_pos, children_pos, og, i):
        obl_case = [
            "",
            f"{parent_pos} -> handle_obl_case{i}({parent_pos}, {current_pos}, {children_pos})",
            f'[ud] f_dep2(merge(merge(?1,"(r<root> :OBL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :CASE (d1<dep1>))"), r_dep1(?3))))))',
            f'[fourlang] f_dep2(f_dep1(merge(merge(merge(?1,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?3)), r_dep2(?2))))',
            ""
        ]

        og.write("\n".join(obl_case))

    def get_trigger(self, word_index, parent, curr, children, og, i):
        parent_dep = parent[2]
        parent_pos = parent[1]
        curr_lemma = curr[0]
        curr_pos = curr[1]
        children_deps = [child[0] for child in children]
        children_lemma = [word_index[child[1]][1]
                          for child in children]
        children_pos = [word_index[child[1]][2]
                        for child in children]

        if "CONJ" in children_deps:
            self.handle_conj(parent_pos, parent_dep, curr_pos,
                             children_pos[children_deps.index("CONJ")], og, i)
        if parent_dep == "ACL_RELCL":
            self.handle_acl_relcl(
                parent_pos, curr_pos, children_pos[children_deps.index("NSUBJ")], og, i)
        if parent_dep == "OBL":
            self.handle_obl_case(
                parent_pos, curr_pos, children_pos[children_deps.index("CASE")], og, i)

    def handle_subgraphs(self, i, word_index, og, dependencies, parent=None):
        _, lemma, pos, children = word_index[i]
        #curr_terminal_lines = get_terminal_lines(lemma, pos)
        if parent:
            self.get_trigger(word_index, parent, (lemma, pos), children, og, i)
        for dep, j in children:
            clemma, cpos = word_index[j][1:3]

            self.handle_subgraphs(
                j, word_index, og, dependencies, parent=(lemma, pos, dep))

    def generate_terminals(self, i, word_index, og):
        _, lemma, pos, children = word_index[i]
        terminal_fss = self.get_default_terminal(lemma, i)

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

    def generate_rules(self, sen, root_i, word_index, og, dependencies):
        root_pos = word_index[root_i][2]
        og.write(f"S! -> ROOT({root_pos})\n")
        og.write("[ud] ?1\n")
        og.write("[fourlang] f_root(f_relation(?1))\n\n")
        self.grammar.generate_grammar(root_i, word_index, og, 2/dependencies)
        og.write("/* terminal rules */\n\n")

        self.grammar.handle_subgraphs(root_i, word_index, og, 3/dependencies)

        self.grammar.generate_terminals(root_i, word_index, og)

        og.write("/* relation terminal rules */\n\n")
        self.grammar.generate_relations(og)

    def make_graph_string(self, i, word_index):
        _, lemma, pos, children = word_index[i]
        graph_string = "({0} / {1}".format(i, lemma)
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
            int(word.id): (
                self.preprocess_word_for_alto(
                    word.text), self.preprocess_word_for_alto(word.lemma),
                word.upos, [])
            for word in sen.words}
        root_index = None
        for word in sen.words:
            if word.head == 0:
                assert root_index is None, 'multiple root elements!'
                root_index = int(word.id)
            else:
                word_index[word.head][-1].append((
                    word.deprel.replace(':', '_').upper(),
                    int(word.id)))

        assert root_index, 'no root element!'
        return word_index, root_index

    def ud_to_irtg(self, doc):
        """
        Gets an ud parse as an input and generates an IRTG from it
        """
        base_fn = os.path.dirname(os.path.abspath(__file__))
        out = os.path.join(base_fn, "dep_to_4lang")
        with open(f"{out}.input", 'w') as of:
            with open(f"{out}.irtg", 'w') as og:
                for sen in doc.sentences:
                    dependencies = len(sen.dependencies)
                    word_index, root_i = self.get_word_index(sen)
                    self.print_input_header(sen, of)
                    of.write("(dummy_0 / dummy_0)\n")
                    graph = self.make_graph_string(root_i, word_index)
                    of.write(graph + "\n")

                    self.print_grammar_header(sen, og)
                    self.generate_rules(
                        sen, root_i, word_index, og, dependencies)
        cmd = "java -Xmx16G -cp /home/adaamko/projects/wikt2def/fourlang/grammars/alto-2.3.6-SNAPSHOT-all.jar de.up.ling.irtg.script.ParsingEvaluator /home/adaamko/projects/wikt2def/fourlang/grammars/dep_to_4lang.input -g /home/adaamko/projects/wikt2def/fourlang/grammars/dep_to_4lang.irtg -I ud -Ofourlang=GraphViz-dot -o /home/adaamko/projects/wikt2def/fourlang/grammars/grammar.output"
        os.system(cmd)

import numpy as np

EXCLUDE = ("punct")


def dep_to_dot(deps, cleaner=None):
    if cleaner is None:
        # can't have this as top-level import because it doesn't work yet
        from fourlang import FourLang
        fl = FourLang()
        cleaner = fl.d_clean
    edges = [
        (tuple(d[1]), d[0], tuple(d[2])) for d in deps if d[0] not in EXCLUDE]
    words = set([e[0] for e in edges] + [e[2] for e in edges])
    lines = [
        "digraph finite_state_machine {",
        "\tdpi=100;"]
    # , "\trankdir=LR;"]
    for word in words:
        print_word = cleaner(word[0])
        lines.append('\t{0}_{1} [shape=rectangle, label="{2}"];'.format(
            print_word, word[1], print_word))
    for dep, dtype, gov in edges:
        dep_word = cleaner(dep[0])
        gov_word = cleaner(gov[0])
        lines.append('\t{0}_{1} -> {2}_{3} [label="{4}"];'.format(
            dep_word, dep[1], gov_word, gov[1], dtype))
    lines.append('}')
    return '\n'.join(lines)


def get_distance(
        src_word, tgt_word, src_emb, tgt_emb, src_word2id, tgt_word2id):
    src_word_emb = src_emb[src_word2id[src_word]]
    tgt_word_emb = tgt_emb[tgt_word2id[tgt_word]]
    score = (tgt_word_emb / np.linalg.norm(tgt_word_emb)).dot(
        src_word_emb / np.linalg.norm(src_word_emb))
    return score

import pandas as pd
import os
import numpy as np


def load_vec(emb_path, nmax=50000):
    vectors = []
    word2id = {}
    with open(emb_path, 'r', encoding='utf-8', newline='\n', errors='ignore') as f:
        next(f)
        for i, line in enumerate(f):
            word, vect = line.rstrip().split(' ', 1)
            vect = np.fromstring(vect, sep=' ')
            assert word not in word2id, 'word found twice'
            vectors.append(vect)
            word2id[word] = len(word2id)
            if len(word2id) == nmax:
                break
    id2word = {v: k for k, v in word2id.items()}
    embeddings = np.vstack(vectors)
    return embeddings, id2word, word2id

def read(lang1, lang2=None, graded=True):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../SemEval2020-Task2-Dev")
    language_name = ""
    if lang2 is None:
        filename = os.path.join(filename, "monolingual")
        language_name = lang1
    else:
        filename = os.path.join(filename, "cross-lingual")
        language_name = "-".join([lang1, lang2]) if lang1[0] < lang2[0] else "-".join([lang2, lang1])
    grad_or_bin = "graded" if graded else "binary"
    filename = os.path.join(filename, grad_or_bin, ".".join([language_name, grad_or_bin, "dev.data.txt"]))
    df = pd.read_csv(filename, delimiter=" ", header=None, names=["premise", "hypothesis", "score"])
    if lang2 is not None:
        df.premise = df.premise.str.replace(lang1 + "_", "")
        df.premise = df.premise.str.replace(lang2 + "_", "")
        df.hypothesis = df.hypothesis.str.replace(lang1 + "_", "")
        df.hypothesis = df.hypothesis.str.replace(lang2 + "_", "")
    return df

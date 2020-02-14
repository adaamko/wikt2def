import pandas as pd
import os


def read(lang1, lang2=None, graded=True):
    filename = "../SemEval2020-Task2-Dev"
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

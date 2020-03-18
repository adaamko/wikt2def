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
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../SemEval2020-Task2-Dev")
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
    # if lang2 is not None:
    #     df.premise = df.premise.str.replace(lang1 + "_", "")
    #     df.premise = df.premise.str.replace(lang2 + "_", "")
    #     df.hypothesis = df.hypothesis.str.replace(lang1 + "_", "")
    #     df.hypothesis = df.hypothesis.str.replace(lang2 + "_", "")
    return df


def get_deps(ud):
    deps = []
    dep_to_id = {}
    ids = 0
    for i in range(0, len(ud) - 2, 2):
        t = ud[i + 1]
        sender = ud[i]
        receiver = ud[i + 2]
        
        if sender not in dep_to_id:
            dep_to_id[sender] = ids
            sender_list = [sender, str(ids)]
            ids+=1
        else:
            sender_id = dep_to_id[sender]
            sender_list = [sender, str(sender_id)]
        
        if receiver not in dep_to_id:
            dep_to_id[receiver] = ids
            receiver_list = [receiver, str(ids)]
            ids+=1
        else:
            receiver_id = dep_to_id[receiver]
            receiver_list = [receiver, str(receiver_id)]
            
        if t.endswith("^-"):
            t = t.strip("^-")
            sender_list, receiver_list = receiver_list, sender_list
        deps.append([t, sender_list, receiver_list])
    return [deps]


def build_graph(df):
    data_frame = pd.DataFrame(columns=["premise", "hypothesis", "score"])
    for i in range(len(df)):
        row = {"score": df.score[i]}
        premise_ud = [df.prem_argleft[i]] + df.premise_ud[i].split("___") + [df.prem_argright[i]]
        hypothesis_ud = [df.hypo_argleft[i]] + df.hypothesis_ud[i].split("___") + [df.hypo_argright[i]]
        row["premise"] = get_deps(premise_ud)
        row["hypothesis"] = get_deps(hypothesis_ud)
        data_frame.loc[i] = row
    return data_frame


def read_sherliic(path_to_data, ud_path=None, keep_context=False, just_ab=True):
    abs_path = os.path.abspath(path_to_data)
    sherliic_data = pd.read_csv(abs_path, delimiter=",",
                                usecols=["premise_relation", "prem_argleft", "prem_middle", "prem_argright",
                                         "hypothesis_relation", "hypo_argleft", "hypo_middle", "hypo_argright",
                                         "is_entailment"])
    if not ud_path:
        sherliic_data = sherliic_data.drop(columns=["premise_relation", "hypothesis_relation"])
    else:
        ud_by_id = pd.read_csv(ud_path, delimiter="\t", header=None, names=["id", "ud"])
        sherliic_data = sherliic_data.join(ud_by_id, on="premise_relation")
        sherliic_data = sherliic_data.rename(columns={"ud": "premise_ud"})
        sherliic_data = sherliic_data.drop(columns=["id", "premise_relation"])

        sherliic_data = sherliic_data.join(ud_by_id, on="hypothesis_relation")
        sherliic_data = sherliic_data.rename(columns={"ud": "hypothesis_ud"})
        sherliic_data = sherliic_data.drop(columns=["id", "hypothesis_relation"])
    if not keep_context:
        sherliic_data = sherliic_data.drop(columns=["prem_argleft", "prem_argright", "hypo_argleft", "hypo_argright"])
    elif just_ab:
        sherliic_data.prem_argleft = sherliic_data.prem_argleft.str.split("[").str[1].str.strip("]")
        sherliic_data.prem_argright = sherliic_data.prem_argright.str.split("[").str[1].str.strip("]")
        sherliic_data.hypo_argleft = sherliic_data.hypo_argleft.str.split("[").str[1].str.strip("]")
        sherliic_data.hypo_argright = sherliic_data.hypo_argright.str.split("[").str[1].str.strip("]")

    sherliic_data = sherliic_data.rename(columns={"prem_middle": "premise", "hypo_middle": "hypothesis",
                                                  "is_entailment": "score"})
    sherliic_data.score[sherliic_data.score == "yes"] = 1
    sherliic_data.score[sherliic_data.score == "no"] = 0
    return sherliic_data

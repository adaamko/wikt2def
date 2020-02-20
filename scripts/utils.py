import numpy as np 

def get_distance(src_word, tgt_word, src_emb, tgt_emb, src_word2id, tgt_word2id):
    src_word_emb = src_emb[src_word2id[src_word]]
    tgt_word_emb = tgt_emb[tgt_word2id[tgt_word]]
    score = (tgt_word_emb / np.linalg.norm(tgt_word_emb)).dot(src_word_emb / np.linalg.norm(src_word_emb))
    return score
    

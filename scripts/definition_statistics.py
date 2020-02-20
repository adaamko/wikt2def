from fourlang.lexicon import Lexicon
from fourlang.stanford_wrapper import StanfordParser


def check_lexicon(lexicon):
    lemma_not_in_lexicon_file = open("lemma_not_in_lexicon.txt", "w")
    lemma_word_def_different_file = open("lemma_word_def_different.txt", "w")
    lemma_not_in_lexicon = []
    lemma_word_def_different = []
    i = 0
    for word in lexicon:
        lemma = sp.lemmatize_word(word)
        if lemma not in lexicon:
            print("{}\t{}\t{}".format(word, lexicon[word], lemma), file=lemma_not_in_lexicon_file)
            lemma_not_in_lexicon.append((word, lemma))
        elif lexicon[lemma] != lexicon[word]:
            print("{}\t{}\t{}\t{}".format(word, lexicon[word], lemma, lexicon[lemma]), file=lemma_word_def_different_file)
            lemma_word_def_different.append({word: lexicon[word], lemma: lexicon[lemma]})
        i += 1
        print(i, len(lexicon))
    print(len(lemma_not_in_lexicon), len(lemma_word_def_different), len(lexicon))


if __name__ == '__main__':
    sp = StanfordParser()
    en = Lexicon(lang="en")
    check_lexicon(en.lexicon)

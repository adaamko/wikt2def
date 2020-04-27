from .parser_wrapper import ParserWrapper


class UdParser():
    def __init__(self, language):
        super().__init__()
        self.wrapper = ParserWrapper()
        self.wrapper.set_parser(language)

    def parse(self, sentence):
        doc = self.wrapper.nlp(sentence)
        deps = doc.sentences[0].dependencies
        sen_deps = []
        for sens in doc.sentences:
            deps = sens.dependencies
            dep_list = []
            for dep in deps:
                curr_dep = []
                curr_dep.append(dep[1])

                if len(sentence.split()) == 1:
                    h = dep[0].text
                    d = dep[2].text
                else:
                    h = dep[0].lemma if dep[0].lemma is not None else dep[0].text
                    d = dep[2].lemma if dep[2].lemma is not None else dep[2].text

                curr_dep.append([h, dep[0].index])
                curr_dep.append([d, dep[2].index])

                dep_list.append(curr_dep)
            sen_deps.append(dep_list)

        return {"deps": sen_deps}

    def lemmatize(self, sentence):
        doc = self.wrapper.nlp(sentence)
        lemmas = []
        words = []
        for sens in doc.sentences:
            for token in sens.tokens:
                words.append(token.text)
                current_lemma = []
                for word in token.words:
                    if word.index in token.index.split('-'):
                        current_lemma += [word.lemma if word.lemma is not None else word.text]
                lemmas.append(current_lemma)

        ret_value = {"lemmas": lemmas, "words": words}

        return ret_value

    def lemmatize_word(self, sentence):
        doc = self.wrapper.nlp(sentence)
        lemma = ""
        for sens in doc.sentences:
            for word in sens.words:
                lemma = " ".join([lemma, word.lemma])

        ret_value = {"lemma": lemma.strip()}

        return ret_value

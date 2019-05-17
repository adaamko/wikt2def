import stanfordnlp


class ParserWrapper():

    def set_parser(language):
        stanfordnlp.download(language, confirm_if_exists=True)
        self.nlp = stanfordnlp.Pipeline(lang=language)
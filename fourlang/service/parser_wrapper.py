import stanfordnlp
import os


class ParserWrapper(object):
    def set_parser(self, language):
        language_model = {"en": "en_ewt", "it": "it_isdt", "de": "de_gsd", "tr": "tr_imst", "hr": "hr_set"}
        if not os.path.exists(os.path.join(os.path.expanduser("~"),
                                           "stanfordnlp_resources/{}_models".format(language_model[language]))):
            stanfordnlp.download(language, confirm_if_exists=True)
        self.nlp = stanfordnlp.Pipeline(lang=language)

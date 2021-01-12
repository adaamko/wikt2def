import stanza
import os


class ParserWrapper(object):
    def set_parser(self, language):
        language_model = {"en": "en_ewt", "it": "it_isdt", "de": "de_gsd", "tr": "tr_imst", "hr": "hr_set"}
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "stanza_resources/resources.json")):
            stanza.download(language)

        self.nlp = stanza.Pipeline(lang=language)

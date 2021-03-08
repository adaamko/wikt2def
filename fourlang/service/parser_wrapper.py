import stanza
import os
from tuw_nlp.text.segmentation import CustomStanzaPipeline

class ParserWrapper(object):
    def set_parser(self, language):
        language_model = {"en": "en_ewt", "it": "it_isdt", "de": "de_gsd", "tr": "tr_imst", "hr": "hr_set"}
        if not os.path.exists(os.path.join(os.path.expanduser("~"),
                                           "stanza_resources/{}_models".format(language_model[language]))):
            stanza.download(language)

        if language == "de":
            self.nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
        else:
            self.nlp = stanza.Pipeline(lang=language)

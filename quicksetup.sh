wget http://sandbox.hlt.bme.hu/~adaamko/sherlic.zip
unzip sherlic.zip
wget http://sandbox.hlt.bme.hu/~adaamko/synonyms.zip
unzip definitions.zip -d fourlang/
wget http://sandbox.hlt.bme.hu/~adaamko/definitions.zip
mkdir fourlang/definitions
unzip definitions.zip -d fourlang/
rm definitions.zip
wget http://sandbox.hlt.bme.hu/~adaamko/semeval.zip
unzip semeval.zip
rm semeval.zip
wget http://sandbox.hlt.bme.hu/~adaamko/de_to_en
mkdir dictionaries
mv de_to_en dictionaries/.
python -m nltk.downloader stopwords
python -m nltk.downloader wordnet
wget http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar
mv alto-2.3.6-SNAPSHOT-all.jar fourlang/grammars/.
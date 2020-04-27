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
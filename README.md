
# wikt2def

This repository contains a tool for automatic extraction of wiktionary definitions. It heavily builds on https://github.com/juditacs/wikt2dict. It also contains code to build semantic graphs from text, based on https://github.com/kornai/4lang.

# fourlang

The repository also contains the code needed to build fourlang graph from raw text. Fourlang grahps rely on the definitions extracted with the wikt2def tool. Currently we support three languages: *English, Italian, and German*.

Also it contains code to reproduce our results on the lexical entailment task on two different dataset (Semeval 2020 and Sherlic). The further sections contain instructions to run our code.

## Requirements

- Python 3.7

## Quick setup

1. Clone the repository
1. Create a python virtual environment

   1. Download [Anaconda](https://conda.io/miniconda.html)
   
   1. Execute the following command to create a virtual environment: `conda create --name YOURENVNAME`

1) Install python dependencies

   ```bash
   pip install -r requirements.txt
   ```
   
2) Download prebuilt dictionary and definitions and place it under *fourlang/definitions/*. Also download the Semeval Dev dataset to reproduce our result.
   ```bash
   bash quicksetup.sh
   ```
3) To be able to build fourlang graphs, the ud service needs to be started (supported languages: en, it, de)
   ```python
   python fourlang/service/ud_service.py -l en -p 5005
   ```
4) If you are only interested in building 4lang graphs, the ```demo.ipynb``` jupyter notebook shows a simple setup and examples.

5) To reproduce our results, first start the servers respectively:
   ```python
   python fourlang/service/ud_service.py -l en -p 5005
   python fourlang/service/ud_service.py -l de -p 5006
   python fourlang/service/ud_service.py -l it -p 5007
   ```
  Then the '''process.py''' file can be used to generate results.


## Usage 

 To run the script:
 ```python
 python process.py -c YOUR_CONFIG_FILE
 ```

 simple configs are provided in the _configs_ folder:

 ```python
 python process.py -c configs/sherlic
 ```

 The result will be placed under the ```output.txt``` file.
 
 
 ## Reproduce our results
 The **Config** column contains the specific config file to run our code with. Also in some cases it contains a specific file with the results (the ones ending with .csv)
 
 ### Semeval
 <div id="table:semeval_results">

| <span>**Lang**</span> | <span>**Method** </span> |     <span>**P**</span> |     <span>**R**</span> |     <span>**F**</span> | Config  |
| :-------------------- | :----------------------- | ---------------------: | ---------------------: | ---------------------: | -: |
|         EN              | always yes               |                  56.33 |                  100.0 |                  72.07 |  |
|         EN              | WordNet                  |                  95.75 |                  88.76 |                  92.12 |semeval_en_wordnet  |
|         EN              | 4lang                    | <span>**96.30**</span> |                  29.21 |                  44.83 | semeval_en_only_4lang |
|         EN              | 4lang\_syn               |                  92.85 |                  36.51 |                  52.41 | semeval_en_OR |
|         EN              | all                      |                  93.22 | <span>**92.69**</span> | <span>**92.95**</span> |semeval_en_OR_voting  |
|         DE              | always yes               |                  37.11 |                  100.0 |                  54.13 |  |
|         DE              | WordNet                  |                  61.61 |                  79.22 |                  69.31 | semeval_de_only_wordnet |
|         DE              | 4lang                    | <span>**88.88**</span> |                  36.36 |                  51.61 | semeval_de_only_4lang |
|         DE              | 4lang\_syn               |                  87.87 |                  37.66 |                  52.72 | semeval_de |
|         DE              | all                      |                  61.86 | <span>**86.36**</span> | <span>**72.08**</span> | semeval_de_voting |
|         IT              | always yes               |                  41.67 |                  100.0 |                  58.82 |  |
|         IT              | WordNet                  |                  88.96 |                  75.88 |                  81.90 | semeval_it_wordnet |
|         IT              | 4lang                    | <span>**93.47**</span> |                  25.29 |                  39.81 |semeval_it_only_4lang  |
|         IT              | 4lang\_syn               |                  81.17 |                  40.58 |                  54.11 | semeval_it_OR |
|         IT              | all                      |                  83.92 | <span>**82.94**</span> | <span>**83.43**</span> | semeval_it_OR_voting |

Performance on the Semeval development set. `4lang` and `4lang_syn` is
our method without and with additional synonym nodes from WordNet and
Wiktionary. `WordNet` is the baseline using WordNet hypernyms, `all` is
the union of `4lang+syn` and `WordNet`

</div>


***Please note that as of now the code doesn't contain caching of the ud parses which may result in longer running time. We plan on optimizing it for further development.***

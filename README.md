***If you are interested in the system submitted to the SemEval 2020 Task 2: Predicting Multilingual and Cross-Lingual (Graded) Lexical Entailment, please go to the Semeval branch for detailed instructions to reproduce our results. The master and the sherlic branch contain futher improvements and experiments on the SherLIiC: A Typed Event-Focused Lexical Inference Benchmark for Evaluating Natural Language Inference dataset.***


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
 

 ### Sherlic
 
<div id="table:sherlic_results">

| <span>**Method** </span>      |    <span>**P**</span> |     <span>**R**</span> |     <span>**F**</span> | <span>**Config**</span> |
| :---------------------------- | --------------------: | ---------------------: | ---------------------: | ---------------------:  |
| always yes                    |                  33.3 |                    100 |                   49.9 | |
| Berant II                     |                  77.4 |                   18.6 |                   30.0 | |
| PPDB                          |                  62.1 |                   24.0 |                   34.7 | |
| WordNet                       |                  38.8 |                   35.7 |                   37.2 | results/results_WordNet_test.csv|
| 4lang                         | <span>**80.4**</span> |                   22.6 |                   35.3 |sherlic |
| 4lang\_syn                    |                  70.0 |                   26.8 |                   38.7 |sherlic_synonyms OR |
| 4lang\_3exp                   |                 71.79 |                  25.35 |                  37.47 | sherlic3|
| 4lang\_3exp\_syn              |                 62.98 | <span>**30.98**</span> | <span>**41.53**</span> |sherlic3_synonyms OR |
| all rules                     |                  39.7 |                   49.9 |                   44.2 | results/all_rules.csv |
| \+ WordNet                    |                  37.2 |                   62.6 |                   46.6 | results/wordnet_and_all_rules.csv |
| \+ 4lang                      |                  42.2 |                   57.9 |                   48.8 | |
| \+ 4lang\_syn                 |                  41.7 |                   59.6 |                   49.0 | |
| \+ WordNet + 4lang            |                  38.7 |                   68.4 |                   49.5 | |
| \+ WordNet + 4lang\_syn       |                  38.9 |                   69.6 |                   49.9 | |
| \+ WordNet + 4lang\_3exp\_syn |                 38.83 |                  70.82 | <span>**50.16**</span> | |
| ESIM                          |                  39.0 |  <span>**83.3**</span> |                   53.1 | |
| w2v + tsg\_rel\_emb           |                  51.8 |                   72.7 |  <span>**60.5**</span> | |

Performance on the SherLlic test set. `4lang` and `4lang_syn` is our
method without and with additional synonym nodes from WordNet and
Wiktionary. `WordNet` is the baseline using WordNet hypernyms, `all` is
the union of `4lang+syns` and `WordNet`. `all rules` is the union of all
rule-based baselines in , `Berant II`  and `PPDB`  are the two strongest
individual rule-based baselines. `ESIM`  is the strongest system
evaluated that wasn’t tuned on SherLlic’s held-out portion and
`w2v+tsg_rel_emb` is the overall strongest system.

To reproduce the result of the original SherLIiC paper, please go to: https://github.com/mnschmit/SherLIiC. We also provide precomputed results in the results directory.

</div>

***Please note that as of now the code doesn't contain caching of the ud parses which may result in longer running time. We plan on optimizing it for further development.***

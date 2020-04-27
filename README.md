# wikt2def

This repository contains a tool for automatic extraction of wiktionary definitions. It heavily builds on https://github.com/juditacs/wikt2dict.

## Usage 

```shell
main.py [-h] [-d] [-x] -w WIKICODES [WIKICODES ...]

optional arguments:
  -h, --help            show this help message and exit
  -d, --download        download data
  -x, --definitions     extract definitions
  -w WIKICODES [WIKICODES ...], --wikicodes WIKICODES [WIKICODES ...]
                        a list of languages
```
                        
# fourlang

The repository also contains the code needed to build fourlang graph from raw text. Fourlang grahps rely on the definitions extracted with the wikt2def tool. Currently we support three languages: *English, Italian, and German*.

## Requirements

- Python 3.7

## Quick setup

1. Clone the repository
1. Create a python virtual environment

   1. Download [Anaconda](https://conda.io/miniconda.html)

   1. Open Anaconda shell and go to the repository root directory

   1. Execute the following command to create a virtual environment: `conda env create`

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
4) The ```demo.ipynb``` jupyter notebook shows a simple setup to create fourlang graphs.

5) To reproduce our results, first start the servers respectively:
   ```python
   python fourlang/service/ud_service.py -l en -p 5005
   python fourlang/service/ud_service.py -l de -p 5006
   python fourlang/service/ud_service.py -l it -p 5007
   ```
   
   Then run the script to parse the data from the ```Semeval Dev``` dataset and run our pipeline:
      ```shell
   usage: semeval.py [-h] -l LANG [LANG ...] -t TYPE [TYPE ...]

    optional arguments:
    -h, --help  show this help message and exit
    -l LANG  --lang the language to run the script on
    -t TYPE  --type choose between binary or graded
   ```
   
   The result will be placed under the ```output.txt`` file.

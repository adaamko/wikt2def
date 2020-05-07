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
                        
## Quick setup

1) To reproduce our results, first start the servers respectively:
   ```python
   python fourlang/service/ud_service.py -l en -p 5005
   python fourlang/service/ud_service.py -l de -p 5006
   python fourlang/service/ud_service.py -l it -p 5007
   ```
   
   Then run the script:
      ```python
   python process.py -c YOUR_CONFIG_FILE
   ```
   simple configs are provided in the _configs_ folder:
   
      ```python
   python process.py -c configs/sherlic
   ```
   
   The result will be placed under the ```output.txt``` file.

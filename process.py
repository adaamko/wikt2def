import argparse
import configparser

import semeval
import sherlic

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-c",
    "--config",
    required=True,
    nargs="+",
    help="the config file path",
    default="configs/default")


args = parser.parse_args()


def main(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    if "sherlic" in config:
        synonyms = config["sherlic"]["synonyms"]
        depth = int(config["sherlic"]["depth"])
        threshold = float(config["sherlic"]["threshold"])
        combine = config["sherlic"]["CombineSynonyms"]
        dataset = config["sherlic"]["dataset"]

        if "blacklist" in config["sherlic"]:
            blacklist = config["sherlic"]["blacklist"].split(",")
            sherlic.run(synonyms, depth, threshold, combine, dataset, blacklist)
        else:
            sherlic.run(synonyms, depth, threshold, combine, dataset)
    elif "semeval" in config:
        synonyms = config["semeval"]["synonyms"]
        filtering = config["semeval"]["filtering"]
        depth = int(config["semeval"]["depth"])
        threshold = float(config["semeval"]["threshold"])
        language = config["semeval"]["language"]
        graded = config["semeval"]["graded"]
        votes = config["semeval"]["votes"] == "True"
        blacklist = config["semeval"]["blacklist"].split(",")
        port = int(config["semeval"]["port"])
        combine = config["semeval"]["CombineSynonyms"]
        if "wordnet_only" in config["semeval"]:
            semeval.run(synonyms, filtering, depth,
                    threshold, language, graded, votes, blacklist, port, combine, True)
        else:
            semeval.run(synonyms, filtering, depth,
                    threshold, language, graded, votes, blacklist, port, combine)


if __name__ == '__main__':
    main(args.config[0])

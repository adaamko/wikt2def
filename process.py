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
        sherlic.run(synonyms, depth, threshold)
    elif "semeval" in config:
        synonyms = config["semeval"]["synonyms"]
        filtering = config["semeval"]["filtering"]
        depth = int(config["semeval"]["depth"])
        threshold = float(config["semeval"]["threshold"])
        language = config["semeval"]["language"]
        graded = config["semeval"]["graded"]
        votes = bool(config["semeval"]["votes"])
        blacklist = config["semeval"]["blacklist"].split(",")
        port = int(config["semeval"]["port"])
        semeval.run(synonyms, filtering, depth,
                    threshold, language, graded, votes, blacklist, port)


if __name__ == '__main__':
    main(args.config[0])

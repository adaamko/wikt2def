import argparse
import codecs
from scipy import stats
import os

def load_lines(filepath):
	return [l.strip() for l in list(codecs.open(filepath, "r", encoding = 'utf8', errors = 'replace').readlines())]

parser = argparse.ArgumentParser(description='Evaluates predicted Lexical Entailment (BINARY, 0/1) scores')
parser.add_argument('preds', help='A path to the file containing word pairs with predicted BINARY scores (format "word1 whitespace word2 whitespace binary_score")')
parser.add_argument('golds', help='A path to the file containing gold standard (i.e., ground truth) binary scores for the same word pairs as in the "preds" file')
args = parser.parse_args()

if not os.path.isfile(args.preds):
	print("Error: File with the predictions not found.")
	exit(code = 1)

if not os.path.isfile(args.golds):
	print("Error: File with the gold standard scores not found.")
	exit(code = 1)

try:
  pred_dict = {l.split()[0] + " :: " + l.split()[1] : int(l.split()[2]) for l in load_lines(args.preds)}
  for pk in pred_dict:
    if pred_dict[pk] != 0 and pred_dict[pk] != 1:
      raise ValueError("Score not binary!") 
except:
  print("Error: misformatted predictions file, make sure every line is in format: 'word_1 whitespace word_2 whitespace pred_score' and that pred_score is 0 or 1.")
  exit(code = 1)

gold_dict = {l.split()[0] + " :: " + l.split()[1] : int(l.split()[2]) for l in load_lines(args.golds)}

if len(pred_dict) != len(gold_dict):
  print("Number of predictions (word pairs in predictions file) incorrect, does not match the number of pairs in the gold standard!")
  exit(code = 1)

pred_scores = []
gold_scores = []

for pk in pred_dict:
  if pk not in gold_dict:
    print("Error: unknown word pair found in predictions file: " + pk)
    exit(code = 2)
  pred_scores.append(pred_dict[pk])
  gold_scores.append(gold_dict[pk])

tp = len([i for i in range(len(pred_scores)) if pred_scores[i] == 1 and gold_scores[i] == 1])
fp = len([i for i in range(len(pred_scores)) if pred_scores[i] == 1 and gold_scores[i] == 0])
fn = len([i for i in range(len(pred_scores)) if pred_scores[i] == 0 and gold_scores[i] == 1])
tn = len([i for i in range(len(pred_scores)) if pred_scores[i] == 0 and gold_scores[i] == 0])

acc = (tp + tn) / len(gold_scores)
p = tp / (tp + fp)
r = tp / (tp + fn)
f = (2 * p * r) / (p + r)

print("Accuracy: " + str(acc))
print("Precision: " + str(p))
print("Recall: " + str(r))
print("F1 score: " + str(f))
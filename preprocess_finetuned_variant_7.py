import pathlib
from transformers import RobertaTokenizer, RobertaModel
import pandas as pd
import json
import os
import torch
import tqdm
from torch import cuda
from torch import nn as nn
import matplotlib.pyplot as plt
from model import VariantSeventFineTuneOnlyClassifier

directory = os.path.dirname(os.path.abspath(__file__))

EMBEDDING_DIRECTORY = 'finetuned_embeddings/variant_7'
FINE_TUNED_MODEL_PATH = 'model/patch_variant_7_finetuned_model.sav'

dataset_name = 'ase_dataset_sept_19_2021.csv'
# dataset_name = 'huawei_sub_dataset.csv'
dataset_name = 'big_vf.csv'
dataset_name = 'test.csv'
CODE_LINE_LENGTH = 256

use_cuda = cuda.is_available()
device = torch.device("cuda:0" if use_cuda else "cpu")
random_seed = 109
torch.manual_seed(random_seed)
torch.cuda.manual_seed(random_seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = True


def get_input_and_mask(tokenizer, code_list):
    inputs = tokenizer(code_list, padding='max_length',
                       max_length=CODE_LINE_LENGTH, truncation=True, return_tensors="pt")

    return inputs.data['input_ids'], inputs.data['attention_mask']


def get_code_version(diff, added_version):
    code = ''
    lines = diff.splitlines()
    # change
    # for line in lines
    for line in lines[:150]:
        mark = '+'
        if not added_version:
            mark = '-'
        if line.startswith(mark):
            line = line[1:].strip()
            if line.startswith(('//', '/**', '/*', '*/')):
                continue
            code = code + line + '\n'

    return code


def get_hunk_embeddings(code_list, tokenizer, code_bert):
    # process all hunks in one
    if len(code_list) == 0:
        return []
    input_ids, attention_mask = get_input_and_mask(tokenizer, code_list)

    with torch.no_grad():
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        embeddings = code_bert(
            input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0, :]
    embeddings = embeddings.tolist()
    return embeddings


def write_embeddings_to_files(removed_embeddings, added_embeddings, removed_url_list, added_url_list):
    url_set = set()
    url_to_removed_embeddings = {}
    for index, url in enumerate(removed_url_list):
        if url not in url_to_removed_embeddings:
            url_set.add(url)
            url_to_removed_embeddings[url] = []
        url_to_removed_embeddings[url].append(removed_embeddings[index])

    url_to_added_embeddings = {}
    for index, url in enumerate(added_url_list):
        if url not in url_to_added_embeddings:
            url_set.add(url)
            url_to_added_embeddings[url] = []
        url_to_added_embeddings[url].append(added_embeddings[index])

    url_to_data = {}
    for url in url_set:
        before_data = []
        after_data = []
        if url in url_to_removed_embeddings:
            before_data = url_to_removed_embeddings[url]
        if url in url_to_added_embeddings:
            after_data = url_to_added_embeddings[url]

        data = {'before': before_data, 'after': after_data}
        url_to_data[url] = data
    for url, data in url_to_data.items():
        file_path = os.path.join(directory, EMBEDDING_DIRECTORY)
        pathlib.Path(file_path).mkdir(parents=True, exist_ok=True)
        file_path = file_path + '/' + url.replace('/', '_') + '.txt'
        json.dump(data, open(file_path, 'w'))


def hunk_empty(hunk):
    if hunk.strip() == '':
        return True

    for line in hunk.split('\n'):
        if line[1:].strip() != '':
            return False

    return True


def get_hunk_from_diff(diff):
    hunk_list = []
    hunk = ''
    for line in diff.split('\n'):
        if line.startswith(('+', '-')):
            hunk = hunk + line + '\n'
        else:
            if not hunk_empty(hunk):    # finish a hunk
                hunk = hunk[:-1]
                hunk_list.append(hunk)
                hunk = ''

    if not hunk_empty(hunk):
        hunk_list.append(hunk)

    return hunk_list


def get_data():
    tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
    model = VariantSeventFineTuneOnlyClassifier()
    if torch.cuda.device_count() > 1:
        print("Let's use", torch.cuda.device_count(), "GPUs!")
        # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
        model = nn.DataParallel(model)

    model.load_state_dict(torch.load(FINE_TUNED_MODEL_PATH))
    # change
    code_bert = model.code_bert

    if torch.cuda.device_count() > 1:
        print("Let's use", torch.cuda.device_count(), "GPUs!")
        # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
        code_bert = nn.DataParallel(code_bert)
    code_bert = code_bert.to(device)

    code_bert.eval()

    print("Reading dataset...")
    df = pd.read_csv(dataset_name)
    df = df[['commit_id', 'repo', 'partition',
             'diff', 'label', 'PL', 'LOC_MOD', 'filename']]
    print(df.shape)
    items = df.to_numpy().tolist()

    url_to_hunk = {}

    for item in items:
        commit_id = item[0]

        repo = item[1]
        url = repo + '/commit/' + commit_id
        diff = item[3]

        if url not in url_to_hunk:
            url_to_hunk[url] = []

        url_to_hunk[url].extend(get_hunk_from_diff(diff))

    removed_code_list = []
    added_code_list = []
    removed_url_list = []
    added_url_list = []
    for url, diff_list in tqdm.tqdm(url_to_hunk.items()):

        file_path = os.path.join(
            directory, EMBEDDING_DIRECTORY + '/' + url.replace('/', '_') + '.txt')
        # co roi thi thoi ?
        if os.path.isfile(file_path):
            # print(file_path)
            continue

        for i, diff in enumerate(diff_list[:1000]):
            removed_code = get_code_version(diff, False)
            if removed_code.strip() != '':
                removed_code_list.append(removed_code)
                removed_url_list.append(url)

            added_code = get_code_version(diff, True)
            if added_code.strip() != '':
                added_code_list.append(added_code)
                added_url_list.append(url)

        if len(removed_code_list) >= 10 or len(added_code_list) >= 10:
            removed_embeddings = get_hunk_embeddings(
                removed_code_list, tokenizer, code_bert)
            added_embeddings = get_hunk_embeddings(
                added_code_list, tokenizer, code_bert)

            write_embeddings_to_files(
                removed_embeddings, added_embeddings, removed_url_list, added_url_list)

            removed_code_list = []
            added_code_list = []
            removed_url_list = []
            added_url_list = []

    if len(removed_code_list) > 0 or len(added_code_list) > 0:
        removed_embeddings = get_hunk_embeddings(
            removed_code_list, tokenizer, code_bert)
        added_embeddings = get_hunk_embeddings(
            added_code_list, tokenizer, code_bert)
        write_embeddings_to_files(
            removed_embeddings, added_embeddings, removed_url_list, added_url_list)


if __name__ == '__main__':
    get_data()

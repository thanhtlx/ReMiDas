from transformers import RobertaTokenizer, RobertaModel
import pandas as pd
import json
import os
import torch
import tqdm
from torch import cuda
from torch import nn as nn
from model import VariantThreeFineTuneOnlyClassifier

EMBEDDING_DIRECTORY = '../finetuned_embeddings/variant_2_cnn'
FINE_TUNED_MODEL_PATH = 'model/patch_variant_2_cnn_finetuned_model.sav'

directory = os.path.dirname(os.path.abspath(__file__))

dataset_name = 'ase_dataset_sept_19_2021.csv'
# dataset_name = 'huawei_sub_dataset_new.csv'

CODE_LINE_LENGTH = 256

use_cuda = cuda.is_available()
device = torch.device("cuda:0" if use_cuda else "cpu")
random_seed = 109
torch.manual_seed(random_seed)
torch.cuda.manual_seed(random_seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = True


def get_input_and_mask(tokenizer, code_list):
    inputs = tokenizer(code_list, padding=True, max_length=CODE_LINE_LENGTH, truncation=True, return_tensors="pt")

    return inputs.data['input_ids'], inputs.data['attention_mask']


def get_code_version(diff, added_version):
    code = ''
    lines = diff.splitlines()
    for line in lines:
        mark = '+'
        if not added_version:
            mark = '-'
        if line.startswith(mark):
            line = line[1:].strip()
            if line.startswith(('//', '/**', '/*', '*/')):
                continue
            code = code + line + '\n'

    return code


def get_file_embeddings(code_list, tokenizer, code_bert):
    # process all lines in one
    input_ids, attention_mask = get_input_and_mask(tokenizer, code_list)

    with torch.no_grad():
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        embeddings = code_bert(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0, :]
    embeddings = embeddings.tolist()
    return embeddings


def write_embeddings_to_files(code_list, url_list, tokenizer, code_bert):
    file_embeddings = get_file_embeddings(code_list, tokenizer, code_bert)
    url_to_embeddings = {}
    for index, url in enumerate(url_list):
        if url not in url_to_embeddings:
            url_to_embeddings[url] = []
        url_to_embeddings[url].append(file_embeddings[index])

    url_to_data = {}
    for url, embeddings in url_to_embeddings.items():
        data = {'embeddings': embeddings}
        url_to_data[url] = data
    for url, data in url_to_data.items():
        file_path = os.path.join(directory, EMBEDDING_DIRECTORY + '/' + url.replace('/', '_') + '.txt')
        json.dump(data, open(file_path, 'w'))


def get_data():
    tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
    model = VariantThreeFineTuneOnlyClassifier()
    if torch.cuda.device_count() > 1:
        print("Let's use", torch.cuda.device_count(), "GPUs!")
        # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
        model = nn.DataParallel(model)

    model.load_state_dict(torch.load(FINE_TUNED_MODEL_PATH))
    code_bert = model.module.code_bert

    if torch.cuda.device_count() > 1:
        print("Let's use", torch.cuda.device_count(), "GPUs!")
        # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
        code_bert = nn.DataParallel(code_bert)
    code_bert = code_bert.to(device)

    code_bert.eval()

    print("Reading dataset...")
    df = pd.read_csv(dataset_name)
    df = df[['commit_id', 'repo', 'partition', 'diff', 'label', 'PL', 'LOC_MOD', 'filename']]
    items = df.to_numpy().tolist()

    url_to_diff = {}

    for item in items:
        commit_id = item[0]
        repo = item[1]
        url = repo + '/commit/' + commit_id
        partition = item[2]
        diff = item[3]
        label = item[4]
        pl = item[5]

        if url not in url_to_diff:
            url_to_diff[url] = []

        url_to_diff[url].append(diff)
       
    code_list = []
    url_list = []
    for url, diff_list in tqdm.tqdm(url_to_diff.items()):
        file_path = os.path.join(directory, EMBEDDING_DIRECTORY + '/' + url.replace('/', '_') + '.txt')
        if os.path.isfile(file_path):
            continue
        for i, diff in enumerate(diff_list):
            removed_code = get_code_version(diff, False)
            added_code = get_code_version(diff, True)

            code = removed_code + tokenizer.sep_token + added_code

            code_list.append(code)
            url_list.append(url)

        if len(url_list) >= 100:
            write_embeddings_to_files(code_list, url_list, tokenizer, code_bert)
            code_list = []
            url_list = []

    write_embeddings_to_files(code_list, url_list, tokenizer, code_bert)


if __name__ == '__main__':
    get_data()

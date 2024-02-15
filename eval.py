import copy
from tqdm import tqdm
import fire
from typing import List

import torch

from utils.model_utils import get_llm
from utils.eval_utils import load_and_eval_ppl, eval_zero_shot
from utils.remove import remove

def eval(
        model_name: str = 'facebook/opt-13b',
        removal_list: List[int] = [4,8,2,13,17,24,36,12],
        save_results: bool = True,
        result_path: str = "sleb_results/eval.txt",
        device: int = 0,
        eval_zeroshot: bool = False
    ):
    
    
    model = get_llm(model_name)
    print(f"Loaded Model: {model.name}")
    model.eval()
    
    original_removal_list = copy.deepcopy(removal_list)
    removal_list.sort()
    model = remove(model, copy.deepcopy(removal_list))
    
    print(f"Starting PPL evaluation...")
    ppl_list = {}
    test_datasets = ['wikitext2', 'c4']
    for dataset in test_datasets:
        ppl = load_and_eval_ppl(model, device, dataset=dataset)

        print(f"{dataset} perplexity = {ppl:.2f}")

        ppl_list[dataset] = ppl
    

    del model
    torch.cuda.empty_cache()

    if eval_zeroshot:
        print(f"Starting Zero-shot tasks evaluation...")
        if '30b' or '66b' or '70b' in model_name:
            parallelize = True
        else:
            parallelize = False

        tasks = ['piqa','winogrande','hellaswag','arc_challenge','arc_easy']
        #tasks = ['piqa', 'winogrande']

        results = eval_zero_shot(model_name, copy.deepcopy(removal_list), tasks, parallelize=parallelize)
        results = results['results']

        for task in tasks:
            print(f"{task}: {results[task]}")
    
    if save_results:
        with open(result_path, 'a') as file:
            sentences = []
            sentences.append(f"Model Name: {model_name}\n")
            sentences.append(f"Block Removal Order: {original_removal_list}\n")
            
            if eval_zeroshot:
                sentences.append(f"WikiText-2 PPL: {ppl_list['wikitext2']:.2f}\n")
                sentences.append(f"C4 PPL: {ppl_list['c4']:.2f}\n")
                sentences.append(f"Zero-shot results: \n")
                for task in tasks:
                    sentences.append(f"{task}: {results[task]}\n")
                sentences.append("\n")
            else:
                sentences.append(f"WikiText-2 PPL: {ppl_list['wikitext2']:.2f} ")
                sentences.append(f"C4 PPL: {ppl_list['c4']:.2f}\n\n")
            
            for sentence in sentences:
                file.write(sentence)

if __name__ == "__main__":
    fire.Fire(eval)
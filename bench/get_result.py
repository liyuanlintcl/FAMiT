import json
import pandas as pd
from tools.pysa import read_pysa_report
from tools.codebase import rename_function
from sklearn.metrics import confusion_matrix, recall_score, precision_score, accuracy_score, f1_score
import seaborn as sns
import matplotlib.pyplot as plt


def draw_confusion_matrix(true_label, pred_label, data_frame, model):
    cm = confusion_matrix(data_frame[true_label], data_frame[pred_label])
    recall = recall_score(data_frame[true_label], data_frame[pred_label])
    precision = precision_score(data_frame[true_label], data_frame[pred_label])
    accuracy = accuracy_score(data_frame[true_label], data_frame[pred_label])
    f1 = f1_score(data_frame[true_label], data_frame[pred_label])
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Good', 'Bad'],
                yticklabels=['Good', 'Bad'])
    plt.xlabel(pred_label)
    plt.ylabel(true_label)
    plt.title(f'acc={accuracy:.3f}, recall={recall:.3f}, precision={precision:.3f}, f1={f1:.3f}')
    plt.savefig(f'../result/bench_result/{true_label} {pred_label} {model} Confusion Matrix.png')
    plt.show()


if __name__ == '__main__':
    pysa_report_issues, _, _ = read_pysa_report('./pysa-runs')
    with open("./pysa-runs/functions.json") as f:
        functions = [json.loads(function_line)["data"]["name"] for function_line in f.readlines()[1:]]
    functions = [(function, function.split(".")[-1].startswith("bad"), function in pysa_report_issues) for function in
                 functions if function.split(".")[-1].startswith("good") or function.split(".")[-1].startswith("bad")]
    df = pd.DataFrame(functions, columns=['function', 'label', 'pysa_result'])

    with open("../result/bench_result/simple_r1_try_1.json", "r", encoding="utf-8") as f:
        bench = json.load(f)

    # with open("../result/bench_result/bench_simple_o1_try_2.json", "r", encoding="utf-8") as f:
    #     bench_ = json.load(f)

    # a = [key for key in bench.keys() if any(x['path_access'] is None for x in bench[key])]
    # b = [key for key in bench.keys() if any(x['taint'] is None for x in bench[key])]

    # df['ai_path'] = df['function'].apply(lambda function:
    #                                      any(x.get('path_access', False) for x in bench.get(rename_function(function), [])))
    # df['ai_taint'] = df['function'].apply(lambda function:
    #                                       any(x.get('taint', False) for x in bench.get(rename_function(function), [])))

    df['ai_taint'] = df['function'].apply(lambda function: bench[function]['taint'] if function in bench else False)
    #
    # df['ai_taint__'] = df['ai_taint_'] & df['ai_taint']

    # df.to_excel('../result/bench_result/bench_gpt_4o_prompt_vote_o1_valid_try_1.xlsx', index=False)

    draw_confusion_matrix('label', 'ai_taint', df, 'simple_r1_try_1')

    df = df[df['ai_taint'].ne(df['label'])].sort_values(by='function')
    print(df)
    print(df.shape)

    func_types = ['branch', 'fields', 'arrays', 'cast', 'exception', 'polymorphism', 'inter', 'long_function', 'loop', 'math', 'complex', 'multi_file', 'recursion', 'sensitivity']
    res_good = [0] * len(func_types)
    res_bad = [0] * len(func_types)
    for _, func_name in df['function'].items():
        func_name_split = func_name.split('.C')
        func_type = func_name_split[0].split('.')[-1]
        if func_name_split[1].split('.')[-1].startswith("bad"):
            res_bad[func_types.index(func_type)] += 1
        else:
            res_good[func_types.index(func_type)] += 1

    print(res_good)
    print(res_bad)

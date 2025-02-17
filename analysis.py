import datetime
import logging
import os
import time

from assistant import CooperationAssistant, SimpleAssistant, Oracle
from tools.codebase import rename_function

now = datetime.datetime.now()
ym = now.strftime('%Y-%m')
day = now.strftime('%d')
hms = now.strftime('%H-%M-%S')

log_file_path = os.path.join('./result/log', ym, day, f'{hms}.log')

log_dir = os.path.dirname(log_file_path)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger('FAMiT')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file_path, encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

deepseek_v3 = {
    "api_key": "xxx",
    "model": "deepseek-chat",
    "api_base": "https://api.deepseek.com/v1"
}


o1_preview = {
    "api_key": "xxx",
    "model": "o1-preview",
    "api_base": "https://api.gptsapi.net/v1"
}

gpt_4o = {
    "api_key": "xxx",
    "model": "gpt-4o",
    "api_base": "https://api.gptsapi.net/v1"
}

claude = {
    "api_key": "xxx",
    "model": "claude-3-5-sonnet-20241022",
    "api_base": "https://api.gptsapi.net/v1"
}

deepseek_r1 = {
    "api_key": "xxx",
    "model": "deepseek-reasoner",
    "api_base": "https://api.deepseek.com/v1"
}


if __name__ == '__main__':
    # simple_assistant = SimpleAssistant(llm_model=deepseek_r1, save_path="./result/bench_result/simple_r1_hs_try_1.json", o1=False)
    # simple_assistant.init(report_dir="D:/Desktop/Lab/Taint-Analysis-By-AI/bench/pysa-runs",
    #                       code_base_path="D:/Desktop/Lab/Taint-Analysis-By-AI/result/code_base.pkl",
    #                       work_dir="D:/Desktop/Lab/Taint-Analysis-By-AI")
    # simple_assistant.analysis_all()

    assistant = CooperationAssistant(llm_model=deepseek_r1, o1=False, all_relative_code=False, voter_num=3, beam_num=1)
    assistant.init(report_dir="D:/Desktop/Lab/Taint-Analysis-By-AI/bench/pysa-runs",
                   code_base_path="D:/Desktop/Lab/Taint-Analysis-By-AI/result/code_base.pkl",
                   work_dir="D:/Desktop/Lab/Taint-Analysis-By-AI",
                   save_path="result/bench_result/r1_hs_rise_without_oracle_3_vote_1_beam_all_code_try_1.json")
    assistant.analysis_all()


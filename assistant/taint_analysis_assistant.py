import json
import logging
import os.path
import re

from assistant.basic_langchain_assistant import BasicAssistant
from functools import partial

logger = logging.getLogger("FAMiT")


class TaintAnalysisAssistant(BasicAssistant):
    def __init__(self, llm_model, o1=False):
        self.out_file_dir = None
        prompt_paths = ["./prompts/BasicTaintAnalysis.txt"]
        validation_path = "./prompts/BasicTaintValidation.txt"
        super().__init__(llm_model, prompt_paths, validation_path, o1=o1)

    def taint_analysis(self, function_name, code):
        return self.send_message(f'The entry function to be analyzed is {function_name}, The related code is as follows, please assuming these lines with "# trace" comment have been executed.:\n{code}')

    def answer_again(self):
        return self.send_message(
            'The answer format is incorrect. Please answer again in the specified format whether the taint propagation occurs and the reason for no taint propagation. The format is as follows:\n{\n"Taint Propagation Occurs": False,\n"Reason for No Taint Propagation": "The variable x has passed through a sanitizer function to remove taint, so f(x) will not cause taint propagation"\n}')

    @staticmethod
    def check_taint_analysis(message):
        taint_analysis_match = re.search(r'"Taint Propagation Occurs"\s*:\s*(\w+)', message)
        false_reason_match = re.search(r'"Reason for No Taint Propagation"\s*:\s*"(.*?)"', message, re.DOTALL)
        if taint_analysis_match:
            taint_analysis = True if taint_analysis_match.group(1) in ['True', 'true'] else False
            if not taint_analysis:
                if false_reason_match:
                    false_reason = false_reason_match.group(1)
                else:
                    return None
            else:
                false_reason = None
            return taint_analysis, false_reason
        else:
            return None

    def analysis(self, func_name, code, beam_num=1):
        self.clean_messages()
        check_func = partial(self.check_result, assistant_answer_again=self.answer_again, check_result_function=self.check_taint_analysis)
        taint_analysis = self.taint_analysis(func_name, code)
        taint, taint_false_reason = self.beam(lambda: taint_analysis, check_func, beam_num)
        return taint, taint_false_reason, taint_analysis

    def rise_without_oracle(self, func_name, code, iter_num, beam_num):
        self.analysis(func_name, code, beam_num)
        analysis_func = partial(self.self_validation)
        check_func = partial(self.check_result, assistant_answer_again=self.answer_again, check_result_function=self.check_taint_analysis)
        return self.vote(analysis_func, check_func, iter_num, beam_num)

import json
import logging
import pickle
import re
from functools import partial
from typing import List, Optional

from assistant.basic_langchain_assistant import BasicAssistant
from tools.codebase import CodeBase
from pydantic import BaseModel, Field

logger = logging.getLogger("FAMiT")


class PathAnalysisAssistant(BasicAssistant):
    def __init__(self, llm_model, o1=False, all_relative_code=False):
        if all_relative_code:
            prompt_paths = ["./prompts/BasicPathAnalysisWithAllCode.txt"]
        else:
            prompt_paths = ["./prompts/BasicPathAnalysis.txt"]
        self.all_relative_code = all_relative_code
        validation_path = "./prompts/BasicPathValidation.txt"
        self.code_base = None
        super().__init__(llm_model, prompt_paths, validation_path, o1=o1)

    def init(self, report_dir, work_dir, code_base_path):
        try:
            with open(code_base_path, 'rb') as f:
                self.code_base = pickle.load(f)
        except FileNotFoundError:
            self.code_base = CodeBase(report_dir, work_dir)
            with open(code_base_path, 'wb') as f:
                pickle.dump(self.code_base, f)

    def path_analysis(self, function_name, codes):
        return self.send_message(f'The entry function to be analyzed is {function_name}, The relevant code is as follows:\n{codes}')

    def answer_again_path_access(self):
        return self.send_message(
            'The answer format is incorrect. Please answer again in the specified format whether the path is reachable and the constraints that cannot be satisfied. The format is as follows: \n{\n"Path Reachable": False,\n"Unresolvable Constraint": "x>0 and x<0 cannot be satisfied simultaneously"\n}')

    def answer_again_need_node(self):
        return self.send_message(
            'The answer format is incorrect. Please answer again in the specified format whether the user needs to provide a function and what function the user should provide. The format is as follows:\n{\n"Code Need": True,\n"Needed Code": ["source__dot_taint__dot_source", "source__dot_taint__dot_sink", "source__dot_taint", "source__dot_cache"]\n}')

    def give_codes(self, codes):
        return self.send_message(f'The code to be provided is as follows. When you come across functions, classes, and modules that you have not seen before or their contents are reduced to pass, be sure to ask me about their code::\n{codes}')

    @staticmethod
    def check_need_code(message):
        need_code_match = re.search(r"Code Need.*:\s*(\w+)", message)
        code_function_match = re.search(r"Needed Code.*:\s*(\[.*?])", message, re.DOTALL)
        if need_code_match:
            need_code = need_code_match.group(1) in ['True', 'true']
            if need_code:
                if code_function_match:
                    try:
                        code_needed_json = code_function_match.group(1)
                        code_needed = json.loads(code_needed_json)
                    except Exception as e:
                        logger.debug(e)
                        return None
                else:
                    return None
            else:
                code_needed = []
            return need_code, code_needed
        else:
            return None

    @staticmethod
    def check_path_access(message):
        path_access_match = re.search(r'"Path Reachable"\s*:\s*(\w+)', message)
        false_reason_match = re.search(r'"Unresolvable Constraint"\s*:\s*"(.*?)"', message, re.DOTALL)
        if path_access_match:
            path_access = True if path_access_match.group(1) in ['True', 'true'] else False
            if not path_access:
                if false_reason_match:
                    false_reason = false_reason_match.group(1)
                else:
                    return None
            else:
                false_reason = None
            return path_access, false_reason
        else:
            return None

    def analysis(self, func_name, code, code_map, beam_num=1):
        self.clean_messages()
        path_access_report = self.path_analysis(func_name, code)
        check_func = partial(self.check_result, assistant_answer_again=self.answer_again_need_node,
                             check_result_function=self.check_need_code)
        if self.all_relative_code:
            check_path = partial(self.check_result, assistant_answer_again=self.answer_again_path_access, check_result_function=self.check_path_access)
            path_access, path_false_reason = self.beam(lambda: path_access_report, check_path, beam_num=beam_num)
        else:
            try:
                while True:
                    _, beam_function_names = self.beam(lambda: path_access_report, check_func, beam_num=beam_num)
                    if beam_function_names is None or len(beam_function_names) == 0:
                        path_access_report = self.app.get_state(self.config).values['messages'][-1].content
                        break
                    function_slice = self.code_base.get_code_by_names(code, beam_function_names, code_map)
                    code += '\n' + function_slice
                    path_access_report = self.give_codes(function_slice)
                path_access, path_false_reason = self.check_result(path_access_report,
                                                                   self.answer_again_path_access,
                                                                   self.check_path_access)
            except Exception as e:
                logger.exception(e)
                path_access, path_false_reason = None, None
        return path_access, path_false_reason, path_access_report

    def rise_without_oracle(self, func_name, code, code_map, iter_num, beam_num):
        self.analysis(func_name, code, code_map, beam_num)
        analysis_func = partial(self.self_validation)
        check_func = partial(self.check_result, assistant_answer_again=self.answer_again_path_access,
                             check_result_function=self.check_path_access)
        result, reason = self.vote(analysis_func, check_func, iter_num, beam_num)
        if not self.all_relative_code:
            code = self.code_base.code_map_conclusion(code_map)
        return result, reason, code

import json
import logging

from .taint_analysis_assistant import TaintAnalysisAssistant
from .path_analysis_assistant import PathAnalysisAssistant
from tools.codebase import rename_function

logger = logging.getLogger("FAMiT")


class CooperationAssistant:
    def __init__(self, llm_model, o1=False, all_relative_code=False, voter_num=3, beam_num=3):
        self.save_path = None
        self.result = {}
        self.voter_num = voter_num
        self.beam_num = beam_num
        self.all_relative_code = all_relative_code
        self.taintAnalysisAssistant = TaintAnalysisAssistant(llm_model=llm_model, o1=o1)
        self.pathAnalysisAssistant = PathAnalysisAssistant(llm_model=llm_model, o1=o1, all_relative_code=all_relative_code)

    def init(self, report_dir, work_dir, code_base_path, save_path=None):
        self.pathAnalysisAssistant.init(report_dir, work_dir, code_base_path)
        self.save_path = save_path if save_path else ''
        try:
            with open(self.save_path, 'r', encoding='utf-8') as file:
                self.result = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.result = {}

    def save(self):
        with open(self.save_path, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, ensure_ascii=False)

    def vote(self, vote_func, vote_func_args=(), vote_func_kwargs=None):
        if vote_func_kwargs is None:
            vote_func_kwargs = {}
        vote_count = 0
        vote_reason = {}
        for i in range(self.voter_num):
            res, reason = vote_func(*vote_func_args, **vote_func_kwargs)
            if res is None:
                continue
            vote_count += res
            if res not in vote_reason:
                vote_reason[res] = []
            vote_reason[res].append(reason)
        res = vote_count > self.voter_num / 2
        reason = vote_reason[res][0]
        return res, reason

    def analysis(self, issue_index, path_index):
        func_name = self.pathAnalysisAssistant.code_base.error_reports[issue_index]
        func_name = rename_function(func_name)
        code_map = {}
        if not self.all_relative_code:
            func_code = self.pathAnalysisAssistant.code_base.get_code_by_function_name(func_name, path_index, code_map) + '\n'
        else:
            func_code = self.pathAnalysisAssistant.code_base.get_function_path_all_relative_code(func_name, path_index)
        logger.info("\n" + func_code)
        if func_name not in self.result:
            self.result[func_name] = []
        if len(self.result[func_name]) <= path_index:
            self.result[func_name].append({})

        path_access, path_false_reason, code = self.pathAnalysisAssistant.rise_without_oracle(func_name, func_code, code_map, self.voter_num, self.beam_num)

        if path_access:
            taint, taint_false_reason = self.taintAnalysisAssistant.rise_without_oracle(func_name, code, self.voter_num, self.beam_num)
        else:
            taint = False
            taint_false_reason = "Path unreachable"

        self.result[func_name][path_index] = {
            'issue_index': issue_index,
            'path_index': path_index,
            'code': code,
            'path_access': path_access,
            'path_false_reason': path_false_reason,
            'taint': taint,
            'taint_false_reason': taint_false_reason,
        }

        self.save()

    def analysis_all(self, begin_issue=0, no_repeat=True):
        for issue_index in range(begin_issue, len(self.pathAnalysisAssistant.code_base.error_reports)):
            func_name = self.pathAnalysisAssistant.code_base.error_reports[issue_index]
            if rename_function(func_name) in self.result and no_repeat:
                continue
            path_trace_items = self.pathAnalysisAssistant.code_base.traces[func_name]
            for path_index in range(len(path_trace_items)):
                logger.info(f"issue_index: {issue_index}, path_index: {path_index}")
                self.analysis(issue_index, path_index)

    def analysis_function(self, function_name):
        try:
            issue_index = self.pathAnalysisAssistant.code_base.error_reports.index(function_name)
            path_trace_items = self.pathAnalysisAssistant.code_base.traces[function_name]
            for path_index in range(len(path_trace_items)):
                logger.info(f"issue_index: {issue_index}, path_index: {path_index}")
                self.analysis(issue_index, path_index)
                self.save()
        except ValueError:
            logger.error(f"{function_name} not found")

import ast
import json
import logging
import os

from assistant.path_analysis_assistant import PathAnalysisAssistant
from assistant.basic_langchain_assistant import BasicAssistant
from assistant.taint_analysis_assistant import TaintAnalysisAssistant
from tools.codebase import rename_function

logger = logging.getLogger("FAMiT")


class SimpleAssistant(TaintAnalysisAssistant, PathAnalysisAssistant):
    def __init__(self, llm_model, save_path, o1=True):
        self.result = None
        self.save_path = save_path
        prompt_paths = ["./prompts/SimpleTaintAnalysis.txt"]
        BasicAssistant.__init__(self, llm_model, prompt_paths, o1=o1)

    def save(self):
        with open(self.save_path, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, ensure_ascii=False)

    def init(self, report_dir, work_dir, code_base_path):
        super().init(report_dir, work_dir, code_base_path)
        try:
            with open(self.save_path, 'r', encoding='utf-8') as file:
                self.result = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.result = {}

    def analyze(self, issue_index):
        self.clean_messages()
        func_name = self.code_base.error_reports[issue_index]
        function_name_split = func_name.split('.')
        for i in range(len(function_name_split) - 1, 0, -1):
            file_name = os.path.join(self.code_base.work_dir, "/".join(function_name_split[:i]) + ".py")
            if os.path.isfile(file_name):
                with open(file_name, "r", encoding='utf-8') as f:
                    source = f.read()
                    parsed_ast = ast.parse(source)
                    count = 0
                    for j in range(i, len(function_name_split)):
                        for node in parsed_ast.body:
                            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == function_name_split[j]:
                                count += 1
                                parsed_ast = node
                                break
                    if count != len(function_name_split) - i:
                        continue
                    break

        taint_analysis = self.taint_analysis(func_name, source)
        try:
            taint, taint_false_reason = self.check_result(taint_analysis, self.answer_again,
                                                          self.check_taint_analysis)
        except Exception as e:
            logger.exception(e)
            taint, taint_false_reason = None, None

        self.result[func_name] = {
            'issue_index': issue_index,
            'code': source,
            'taint': taint,
            'taint_false_reason': taint_false_reason,
        }
        self.save()

    def analysis_all(self, begin_issue=0, no_repeat=True):
        for issue_index in range(begin_issue, len(self.code_base.error_reports)):
            func_name = self.code_base.error_reports[issue_index]
            if func_name in self.result and no_repeat:
                continue
            path_trace_items = self.code_base.traces[func_name]
            for path_index in range(len(path_trace_items)):
                logger.info(f"issue_index: {issue_index}")
                self.analyze(issue_index)

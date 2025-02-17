import ast
import os
import sys
import logging

import ast_comments

from tools.pysa import read_pysa_report, read_call_graph
from tools.code_rewrite import FunctionRename, VariableRename
from tools.code_visitor import VariableVisitor, RelativeVisitor

logger = logging.getLogger('AI-Taint-Analysis')


def rename_function(function_name, pos=None):
    if function_name.endswith('.__init__'):
        function_name = function_name.rstrip('.__init__')
    new_name = function_name.replace('.', '__dot_').replace('$', '__dollar_')
    if pos is None:
        return new_name
    else:
        return new_name + f'__pos_{pos[0]}_{pos[1]}_{pos[2]}_'


class CodeBase(object):
    def __init__(self, report_dir, work_dir):
        error_reports, traces, sinks = read_pysa_report(report_dir)
        self.sinks = {}
        self.callgraph = read_call_graph(os.path.join(report_dir, "call-graph.json"), work_dir)
        self.function_rename_map = {}
        self.get_function_rename_map()
        self.traces = {}
        self.work_dir = work_dir
        self.path_map = {}
        self.get_path_map()
        self.error_reports = error_reports
        sys.path.append(work_dir)
        self.mark_path(traces, self.traces)
        self.mark_path(sinks, self.sinks, sink=True)
        # self.function_cfg = dict()
        # self.function_line_offset = dict()
        # self.function_ast = dict()
        # from .rda import RDA
        # self.rda: RDA = RDA(self)
        # from .slicer import Slicer
        # self.slicer: Slicer = Slicer(self)

    def get_path_map(self):
        for root, dirs, files in os.walk(self.work_dir):
            rel_path = os.path.relpath(root, self.work_dir)
            for file in files:
                if file == '__init__.py':
                    with open(os.path.join(root, file), 'r') as f:
                        node = ast.parse(f.read())
                        variables_rename = {}
                        VariableVisitor(variables_rename, rel_path.replace('/', '.'), 1).visit(node)
                        for var_name, var_rename in variables_rename.items():
                            self.path_map[rel_path.replace('/', '__dot_') + '__dot_' + var_name] = var_rename

    def get_function_rename_map(self):
        for function_name, callgraph_item in self.callgraph.items():
            self.function_rename_map[rename_function(function_name)] = function_name
            for call_func_pos, call_function_names in callgraph_item.items():
                for call_function_name in call_function_names:
                    if not call_function_name.endswith('.__init__'):
                        self.function_rename_map[rename_function(call_function_name)] = call_function_name
                if len(call_function_names) > 1:
                    call_func_pos = call_func_pos.split("-")
                    start_pos = call_func_pos[0].split(":")
                    end_pos = call_func_pos[1].split(":")
                    self.function_rename_map[
                        rename_function(function_name, (start_pos[0], start_pos[1], end_pos[1]))] = [
                        rename_function(call_function_name) for call_function_name in call_function_names]

    def get_path_trace_items(self, function_name, path_index):
        if function_name in self.function_rename_map:
            function_name = self.function_rename_map[function_name]
        if path_index is None:
            if function_name in self.sinks:
                trace_items = self.sinks[function_name][0]
            else:
                return dict()
        else:
            trace_items = self.traces[function_name][path_index]
        new_trace_items = dict()
        for line, item in trace_items.items():
            new_trace_items[line] = item.rstrip().rstrip(',').rstrip('|') + '\n'
        return new_trace_items

    def get_function_by_name(self, function_name, rewrite=True, path_index=None):
        if function_name in self.function_rename_map:
            function_name = self.function_rename_map[function_name]
            if isinstance(function_name, list):
                return function_name

        function_name_split = function_name.split('.')
        for i in range(len(function_name_split) - 1, 0, -1):
            file_name = os.path.join(self.work_dir, "/".join(function_name_split[:i]) + ".py")
            try:
                with open(file_name, "r", encoding='utf-8') as f:
                    source = f.read()
                    parsed_ast = ast.parse(source)
                    variables_rename = {}
                    VariableVisitor(variables_rename, ".".join(function_name_split[:i])).visit(parsed_ast)
                    for j in range(i, len(function_name_split)):
                        for node in parsed_ast.body:
                            if (isinstance(node, ast.ClassDef) or isinstance(node, ast.FunctionDef)) and node.name == \
                                    function_name_split[j]:
                                parsed_ast = node
                                break
                    if isinstance(parsed_ast, ast.Module):
                        parsed_ast = ast.FunctionDef(name=function_name_split[-1], args=[], body=parsed_ast.body,
                                                     lineno=parsed_ast.body[0].lineno,
                                                     end_lineno=parsed_ast.body[-1].end_lineno)
                    if rewrite:
                        call_new_names = self.callgraph[function_name] if function_name in self.callgraph else None
                        def_new_name = (parsed_ast.name, rename_function(function_name))
                        trace_items = self.get_path_trace_items(function_name, path_index)
                        parsed_ast = FunctionRename(def_new_name=def_new_name, call_new_names=call_new_names,
                                                    trace_items=trace_items).visit(parsed_ast)
                        parsed_ast = VariableRename(variables_rename).visit(parsed_ast)
                        if isinstance(parsed_ast, ast.Module):
                            parsed_ast = parsed_ast.body[0]
                    else:
                        parsed_ast = (
                            source.split("\n")[parsed_ast.lineno - 1: parsed_ast.end_lineno], parsed_ast.lineno)
                    return parsed_ast
            except FileNotFoundError:
                continue
        return None

    @staticmethod
    def get_code_by_function(parsed_ast, relative_name=None):
        function_source = ast_comments.unparse(parsed_ast)
        if relative_name is not None:
            RelativeVisitor(relative_name).visit(parsed_ast)
        return function_source, parsed_ast.lineno

    def get_code_by_function_name(self, function_name, path_index=None, code_map=None, relative_name=None):
        function = self.get_function_by_name(function_name, path_index=path_index)
        if function is None:
            if function_name in self.function_rename_map:
                return f'function {function_name} actually is {self.function_rename_map[function_name]}\n'
            else:
                return None
        if not (function_name in code_map and isinstance(code_map[function_name], ast.FunctionDef) and not isinstance(
                code_map[function_name].body[0], ast.Pass)):
            code_map[function_name] = function
        code, _ = self.get_code_by_function(function, relative_name)
        return code

    def get_code_by_names(self, codes, names, code_map, relative_name=None):
        res = ''
        for name in names:
            name = name.split('.')[-1]
            if name not in codes and relative_name is None:
                continue
            if name not in self.function_rename_map or (not isinstance(self.function_rename_map[name], list) and self.function_rename_map[name].endswith('__init__')):
                res += self.get_code_by_name(name, code_map, relative_name) + '\n'
            elif isinstance(self.function_rename_map[name], list):
                res += f'{name} may actually correspond to more than one function, and here are the functions it may correspond to:\n\n'
                for func_name in self.function_rename_map[name]:
                    res += self.get_code_by_function_name(func_name, code_map=code_map,
                                                          relative_name=relative_name) + '\n\n'
            else:
                code = self.get_code_by_function_name(name, code_map=code_map, relative_name=relative_name)
                if code:
                    res += f'The code of {name} is as follows:\n{code}\n\n'
                else:
                    res += f'{name} do not need to be concerned\n\n'
        res.rstrip()
        return res

    def get_code_by_name(self, name, code_map, relative_name: set = None):
        def get_module_code(filename, name_splits):
            with open(filename, "r", encoding='utf-8') as f_:
                source_ = f_.read()
                node_ = ast.parse(source_)
                variables_rename_ = {}
                VariableVisitor(variables_rename_, ".".join(name_splits)).visit(node_)
                node_ = VariableRename(variables_rename_, name).visit(node_)
            return node_

        def get_module_file_and_dir(filedir):
            files_ = []
            dirs_ = []
            for filename in os.listdir(filedir):
                file_path = os.path.join(filedir, filename)
                if os.path.isfile(file_path):
                    files_.append(name + '__dot_' + filename)
                if os.path.isdir(file_path):
                    dirs_.append(name + '__dot_' + filename)
            files_ = ', '.join(files_) if len(files_) > 0 else 'None'
            dirs_ = ', '.join(dirs_) if len(dirs_) > 0 else 'None'
            return files_, dirs_

        name_split = name.split('__dot_')
        file_name = os.path.join(self.work_dir, "/".join(name_split) + ".py")
        if os.path.isfile(file_name):
            node = get_module_code(file_name, name_split)
            if not (name in code_map and isinstance(code_map[name], ast.FunctionDef) and not isinstance(
                    code_map[name].body[0], ast.Pass)):
                code_map[name] = node
            return f'The code of {name} is as follows, the "pass" here is just for simplification, not the content is really "pass", if you want to know the specific content, you must continue to ask questions:\n{ast.unparse(node)}\n'

        file_dir = os.path.join(self.work_dir, "/".join(name_split))
        if os.path.isfile(file_dir + '/__init__.py'):
            file_name = file_dir + '/__init__.py'
            files, dirs = get_module_file_and_dir(file_dir)
            node = get_module_code(file_name, name_split)
            if not (name in code_map and isinstance(code_map[name], ast.FunctionDef) and not isinstance(
                    code_map[name].body[0], ast.Pass)):
                code_map[name] = node
            return f'{name} is a module, it contains files: {files}, dirs: {dirs}, and the __init__.py is as follows, the "pass" here is just for simplification, not the content is really "pass", if you want to know the specific content, you must continue to ask questions:\n{ast.unparse(node)}\n'

        if name in self.path_map:
            name = self.path_map[name]
            name_split = name.split('__dot_')

        for i in range(len(name_split) - 1, 0, -1):
            file_name = os.path.join(self.work_dir, "/".join(name_split[:i]) + ".py")
            if os.path.isfile(file_name):
                with open(file_name, "r", encoding='utf-8') as f:
                    source = f.read()
                    parsed_ast = ast.parse(source)
                    variables_rename = {}
                    VariableVisitor(variables_rename, ".".join(name_split[:i])).visit(parsed_ast)
                    count = 0
                    for j in range(i, len(name_split)):
                        for node in parsed_ast.body:
                            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name_split[j]:
                                count += 1
                                parsed_ast = node
                                break
                    if count != len(name_split) - i:
                        continue
                    if isinstance(parsed_ast, ast.ClassDef):
                        parsed_ast = VariableRename(variables_rename, name).visit(parsed_ast)
                        code_map[name] = parsed_ast
                        res = f'The code of {name} is as follows, the "pass" here is just for simplification, not the content is really "pass", if you want to know the specific content, you must continue to ask questions:\n{ast.unparse(parsed_ast)}\n'
                    if isinstance(parsed_ast, ast.FunctionDef):
                        parsed_ast = VariableRename(variables_rename).visit(parsed_ast)
                        if not (name in code_map and isinstance(code_map[name], ast.FunctionDef) and not isinstance(
                                code_map[name].body[0], ast.Pass)):
                            code_map[name] = parsed_ast
                        res = f'The code of {name} is as bellows:\n{ast.unparse(parsed_ast)}\n\n'
                    if relative_name is not None:
                        RelativeVisitor(relative_name).visit(parsed_ast)
                    return res
        return f'{name} do not need to be concerned\n'

    def get_function_path_all_relative_code(self, func_name, path_index):
        code_map = dict()
        relative_name = set()
        codes = self.get_code_by_function_name(func_name, path_index, code_map, relative_name) + '\n'
        while True:
            need_relative_name = []
            for relative_item in relative_name:
                if relative_item not in code_map:
                    need_relative_name.append(relative_item)
            if len(need_relative_name) == 0:
                break
            relative_name = set()
            self.get_code_by_names(codes, need_relative_name, code_map, relative_name)
        return self.code_map_conclusion(code_map)

    @staticmethod
    def code_map_conclusion(code_map):
        res = ''
        class_func = []
        for name, node in code_map.items():
            if isinstance(node, (ast.ClassDef, ast.Module)):
                new_body = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        if child.name in code_map:
                            new_body.append(code_map[child.name])
                            class_func.append(child.name)
                        elif not isinstance(child.body[0], ast.Pass):
                            new_body.append(child)
                    else:
                        new_body.append(child)
                node.body = new_body
                res += ast_comments.unparse(node) + '\n\n'
        for name, node in code_map.items():
            if isinstance(node, ast.FunctionDef) and name not in class_func:
                res += ast_comments.unparse(node) + '\n\n'
        return res

    @staticmethod
    def get_trace_from_code(code):
        code_lines = code.split('\n')
        trace = {}
        for i, line in enumerate(code_lines):
            index = line.find('  # trace')
            if index != -1:
                trace[i + 1] = line[index:] + '\n'
        return trace

    def mark_path(self, traces, modified_traces, sink=False):
        """遍历traces，获取每个污点传播时的代码、对应行号、起始位置和结束位置(同一行的放在一个数组)"""
        for function_name, trace in traces.items():
            modified_traces[function_name] = []
            function = self.get_function_by_name(function_name, rewrite=False)
            if function:
                code_lines, start_line = function
                trace_rename = {}
                if function_name in self.callgraph:
                    for call_func_pos, call_func_names in self.callgraph[function_name].items():
                        call_func_pos = call_func_pos.split("-")
                        start_pos = call_func_pos[0].split(":")
                        end_pos = call_func_pos[1].split(":")
                        if len(call_func_names) == 1:
                            trace_rename[f'{start_pos[0]}:{start_pos[1]}:{end_pos[1]}'] = rename_function(
                                call_func_names[0])
                        else:
                            trace_rename[f'{start_pos[0]}:{start_pos[1]}:{end_pos[1]}'] = rename_function(function_name,
                                                                                                          (start_pos[0],
                                                                                                           start_pos[1],
                                                                                                           end_pos[1]))
                if sink:
                    trace = [trace]
                for paths in trace:
                    modified_traces[function_name].append({})
                    for i, path in enumerate(paths):
                        line_number = path["line"]
                        pos = f'{line_number}:{path["start"]}:{path["end"]}'
                        if pos in trace_rename:
                            call_func_name = trace_rename[pos]
                            func_len = len(
                                code_lines[line_number - start_line][path["start"]: path["end"]].split("(")[0])
                            trace_item = call_func_name + code_lines[line_number - start_line][
                                                          path["start"] + func_len: path["end"]]
                        else:
                            trace_item = code_lines[line_number - start_line][path["start"]: path["end"]]
                        if line_number not in modified_traces[function_name][-1]:
                            modified_traces[function_name][-1][line_number] = "  # trace "
                        if i == 0 and not sink:
                            modified_traces[function_name][-1][line_number] += 'source '
                        if i == len(paths) - 1 or sink:
                            if modified_traces[function_name][-1][line_number].endswith(', '):
                                modified_traces[function_name][-1][line_number] = modified_traces[function_name][-1][
                                                                                  line_number].rstrip(', ') + ' | '
                            if sink:
                                modified_traces[function_name][-1][line_number] += 'one path '
                            modified_traces[function_name][-1][line_number] += 'sink '
                        if trace_item != '':
                            modified_traces[function_name][-1][line_number] += trace_item
                            if i == 0:
                                modified_traces[function_name][-1][line_number] += ' | '
                            elif i != len(paths) - 1:
                                modified_traces[function_name][-1][line_number] += ', '
                    if len(modified_traces[function_name][-1]) == 0:
                        modified_traces[function_name].pop()
            if len(modified_traces[function_name]) == 0:
                modified_traces.pop(function_name)

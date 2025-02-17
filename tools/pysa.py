import ast
import json
import os
import re
import builtins


def read_pysa_report(report_dir):
    errors_file = os.path.join(report_dir, "errors.json")
    with open(errors_file, 'r') as f:
        line = f.readline()
    error_reports = []
    for error in json.loads(line):
        error_reports.append(error["define"])

    taint_output_file = os.path.join(report_dir, "taint-output.json")
    with open(taint_output_file, 'r') as f:
        lines = f.readlines()
    traces = {}
    sinks = {}
    for line in lines[1:]:
        taint = json.loads(line)
        function_name = taint["data"]["callable"]
        if taint["kind"] == "issue":
            if function_name not in traces:
                traces[function_name] = []
            paths = traces[function_name]
            taint_sink = []
            if 'origin' in taint["data"]["traces"][1]["roots"][0]:
                taint_sink = taint["data"]["traces"][1]["roots"][0]["origin"]
            elif 'call' in taint["data"]["traces"][1]["roots"][0]:
                taint_sink = taint["data"]["traces"][1]["roots"][0]["call"]["position"]
            for path in taint["data"]["traces"][0]["roots"]:
                if "tito_positions" in path:
                    paths.append(path["tito_positions"] + [taint_sink])
                elif "call" in path:
                    paths.append([path["call"]["position"], taint_sink])
                else:
                    paths.append([path["origin"], taint_sink])
        if taint["kind"] == "model":
            if "sinks" in taint["data"] and 'taint' in taint["data"]["sinks"][0]:
                if function_name not in sinks:
                    sinks[function_name] = []
                for sink in taint["data"]["sinks"][0]['taint']:
                    if 'origin' in sink:
                        sinks[function_name].append(sink['origin'])
                    if 'call' in sink:
                        sinks[function_name].append(sink['call']["position"])

    return error_reports, traces, sinks


def read_call_graph(call_graph_file, work_dir):
    from tools.code_visitor import PositionVisitor
    with open(call_graph_file, 'r') as f:
        lines = f.readlines()

    call_graph = {}
    for line in lines[1:]:
        call_graph_data = json.loads(line)["data"]
        if call_graph_data['filename'] == '*':
            continue
        with open(os.path.join(work_dir, call_graph_data['filename']), 'r', encoding='utf-8') as f:
            code = f.read()
            parsed = ast.parse(code)
        call_graph[call_graph_data['callable']] = {}
        call_graph_item = call_graph[call_graph_data['callable']]
        for pos, call in call_graph_data["calls"].items():
            if 'singleton' in call and 'call' in call['singleton']:
                singleton_call = call['singleton']['call']
                if 'calls' in singleton_call:
                    call_graph_item[pos] = [handle(singleton_call_['target']) for singleton_call_ in singleton_call['calls']]
                if 'init_calls' in singleton_call and 'new_calls' in singleton_call:
                    call_graph_item[pos] = [handle(singleton_call_['target']) for singleton_call_ in singleton_call['init_calls']]
            if 'compound' in call:
                compound_visitor = PositionVisitor(pos)
                compound_visitor.visit(parsed)
                compound_node = compound_visitor.result
                if isinstance(compound_node, ast.Call):
                    for function_name, compound in call['compound'].items():
                        if 'call' in compound and 'calls' in compound['call']:
                            if not function_name.startswith(('__', '$')) and ast.unparse(compound_node.func).endswith(function_name):
                                call_graph_item[pos] = [handle(compound_call_['target']) for compound_call_ in compound['call']['calls']]
            if pos in call_graph_item:
                call_graph_item[pos] = [call for call in call_graph_item[pos] if call is not None]
                if len(call_graph_item[pos]) == 0:
                    call_graph_item.pop(pos)
                else:
                    call_graph_item[pos] = list(set(call_graph_item[pos]))
    return call_graph


def handle(call):
    overrides = re.search(r"Overrides\{(.+?)}", call)
    res = call
    if overrides:
        res = overrides.group(1)
    if res.split('.')[0] in dir(builtins):
        res = None
    return res

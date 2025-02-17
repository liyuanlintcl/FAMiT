import ast
from copy import copy
from typing import Tuple, Dict, List
import ast_comments


class PassRewriter(ast.NodeTransformer):
    def visit_If(self, node):
        values = []
        if isinstance(node.body[0], ast.Pass):
            values.append(ast.Assert(test=ast.UnaryOp(op=ast.Not(), operand=node.test)))
            for stmt in node.orelse:
                values.append(self.visit(stmt))
        elif len(node.orelse) > 0 and isinstance(node.orelse[0], ast.Pass):
            values.append(ast.Assert(test=node.test))
            for stmt in node.body:
                values.append(self.visit(stmt))
        else:
            self.generic_visit(node)
            values = node
        return values

    def visit_For(self, node):
        if isinstance(node.body[0], ast.Pass) and len(node.body) == 1:
            return node.orelse


class FunctionRename(ast.NodeTransformer):
    def __init__(self, def_new_name: Tuple[str, str] = None, call_new_names: Dict[str, List[str]] = None,
                 trace_items: Dict[int, str] = None):
        self.values_change = []
        self.def_new_name = def_new_name
        self.call_new_names = call_new_names
        self.trace_items = trace_items

    def visit_FunctionDef(self, node):
        if self.def_new_name is not None and self.def_new_name[0] == node.name:
            node.name = self.def_new_name[1]
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        assignment = None
        if self.call_new_names is not None:
            node_call_pos = f'{node.lineno}:{node.col_offset}-{node.end_lineno}:{node.end_col_offset}'
            if node_call_pos in self.call_new_names:
                call_new_names = self.call_new_names[node_call_pos]
                from tools.codebase import rename_function
                if len(call_new_names) == 1:
                    name = ast.Name(rename_function(call_new_names[0]))
                else:
                    name = ast.Name(
                        rename_function(self.def_new_name[1], (node.lineno, node.col_offset, node.end_col_offset)))
                    assignment = ast.Assign(
                        targets=[name],
                        value=copy(node.func),
                        lineno=node.lineno - 1
                    )
                if isinstance(node.func, ast.Attribute):
                    node.func.attr = name.id
                elif isinstance(node.func, ast.Name):
                    node.func = name
        for arg in node.args:
            self.generic_visit(arg)
        for keyword in node.keywords:
            self.generic_visit(keyword)
        if assignment:
            assignment.targets[0] = node.func
            self.values_change.append(assignment)
        return node

    def generic_visit(self, node):
        for field, old_value in ast.iter_fields(node):
            if field in ['body', 'orelse', 'finalbody', 'handlers']:
                self.get_new_values(node, field)
        for field, old_value in ast.iter_fields(node):
            if field not in ['body', 'orelse', 'finalbody', 'handlers']:
                if isinstance(old_value, list):
                    new_values = []
                    for value in old_value:
                        if isinstance(value, ast.AST):
                            value = self.visit(value)
                            if value is None:
                                continue
                            elif not isinstance(value, ast.AST):
                                new_values.extend(value)
                                continue
                        new_values.append(value)
                    old_value[:] = new_values
                elif isinstance(old_value, ast.AST):
                    new_node = self.visit(old_value)
                    if new_node is None:
                        delattr(node, field)
                    else:
                        setattr(node, field, new_node)
        return node

    def get_new_values(self, node, filed_name):
        old_values = getattr(node, filed_name)
        if isinstance(old_values, list):
            new_values = []
            for stmt in old_values:
                self.visit(stmt)
                new_values.extend(self.values_change)
                new_values.append(stmt)
                if stmt.lineno in self.trace_items:
                    new_values.append(ast_comments.Comment(value=self.trace_items[stmt.lineno].rstrip(), inline=True))
                    self.trace_items.pop(stmt.lineno)
                self.values_change = []
            old_values[:] = new_values
        else:
            self.visit(old_values)


class MultiValueRewriter(ast.NodeTransformer):
    def __init__(self, traced_vars=None, traced_return=None):
        if traced_return is None:
            traced_return = []
        if traced_vars is None:
            traced_vars = []
        self.traced_vars = traced_vars
        self.traced_return = traced_return
        self.callees = []
        self.traced_return_vars = []

    def visit_Assign(self, node):
        target = node.targets[0]
        value = node.value
        if isinstance(target, ast.Tuple):
            traced_vars = []
            for i, elt in enumerate(target.elts):
                if ast_comments.unparse(elt) in self.traced_vars:
                    traced_vars.append(elt)
                    self.traced_return.append(i)
            if len(traced_vars) == 1:
                node.targets[0] = traced_vars[0]
            else:
                node.targets[0] = ast.Tuple(traced_vars)
        else:
            self.traced_return = [-1]
        if isinstance(value, ast.Tuple):
            traced_return = []
            for i, elt in enumerate(value.elts):
                if i in self.traced_return:
                    self.visit(elt)
                    traced_return.append(elt)
            if len(traced_return) == 1:
                node.value = traced_return[0]
            else:
                node.value = ast.Tuple(traced_return)
        else:
            self.visit(value)
        return node

    def visit_Call(self, node):
        self.callees.append(ast_comments.unparse(node.func).split('.')[-1])
        for arg in node.args:
            self.visit(arg)
        for arg in node.keywords:
            self.visit(arg)
        return node

    def visit_Return(self, node):
        if len(self.traced_return) == 0:
            node.value = None
        if isinstance(node.value, ast.Tuple):
            traced_return = []
            for i, elt in enumerate(node.value.elts):
                if i in self.traced_return or -1 in self.traced_return:
                    self.traced_return_vars.append(ast_comments.unparse(elt))
                    self.visit(elt)
                    traced_return.append(elt)
            if len(traced_return) == 1:
                node.value = traced_return[0]
            else:
                node.value = ast.Tuple(traced_return)
        elif isinstance(node.value, ast.AST):
            self.visit(node.value)
        return node


class VariableRename(ast.NodeTransformer):
    def __init__(self, variables_rename, module_name=None, class_detail=True):
        self.from_attr = False
        self.attr_rename = None
        self.variables_rename = {}
        self.module_name = module_name
        self.class_detail = class_detail
        for k, v in variables_rename.items():
            names = self.variables_rename
            k_split = k.split('.')
            for i, it in enumerate(k_split):
                if it not in names:
                    names[it] = {}
                if i == len(k_split) - 1:
                    names[it]['__name__'] = v
                else:
                    names = names[it]

    def visit_Name(self, node):
        if node.id in self.variables_rename:
            if not self.from_attr and '__name__' in self.variables_rename[node.id]:
                node.id = self.variables_rename[node.id]['__name__']
            else:
                self.attr_rename = self.variables_rename[node.id]
        return node

    def visit_Attribute(self, node):
        self.from_attr = True
        self.visit(node.value)
        if self.attr_rename is not None:
            if '__name__' in self.attr_rename:
                if len(self.attr_rename) == 1:
                    node.value = ast.Name(self.attr_rename['__name__'])
                    self.attr_rename = None
                else:
                    if node.attr in self.attr_rename:
                        self.attr_rename = self.attr_rename[node.attr]
                    else:
                        node.value = ast.Name(self.attr_rename['__name__'])
                        self.attr_rename = None
            else:
                if node.attr in self.attr_rename:
                    self.attr_rename = self.attr_rename[node.attr]
                else:
                    self.attr_rename = None
        self.from_attr = False
        return node

    def visit_ClassDef(self, node):
        node.name = self.variables_rename[node.name]['__name__']
        for base in node.bases:
            self.visit(base)
        for decorator in node.decorator_list:
            self.visit(decorator)
        if self.class_detail:
            for body in node.body:
                self.visit(body)
        else:
            node.body = [ast.Pass()]
        return node

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            self.visit(decorator)
        if self.module_name is not None:
            node.name = self.module_name + '__dot_' + node.name
            if not node.name.endswith('__init__'):
                node.body = [ast.Pass()]
        else:
            super().generic_visit(node)
        return node

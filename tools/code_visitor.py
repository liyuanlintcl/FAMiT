import ast

import ast_comments
from enum import Enum


class CallVisitor(ast.NodeVisitor):
    def __init__(self, function_call_redef_args, statement_call_function_args, var, codebase):
        self.function_call_redef_args = function_call_redef_args
        self.statement_call_function_args = statement_call_function_args
        self.var = var
        self.codebase = codebase

    def visit_Call(self, node):
        call_name = ast_comments.unparse(node.func).rstrip().split('.')[-1]
        if call_name in self.codebase.function_rename_map and isinstance(self.codebase.function_rename_map[call_name],
                                                                         list):
            call_names = self.codebase.function_rename_map[call_name]
        else:
            call_names = [call_name]
        for call_name in call_names:
            if call_name not in self.function_call_redef_args:
                self.function_call_redef_args[call_name] = list()
            if node in self.statement_call_function_args:
                if '<ret>' in self.statement_call_function_args[node] and '<ret>' not in self.function_call_redef_args[call_name]:
                    self.function_call_redef_args[call_name].append('<ret>')
                if self.var in self.statement_call_function_args[node]:
                    self.function_call_redef_args[call_name].append(self.statement_call_function_args[node][self.var])
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword)


class DefUseState(Enum):
    DEF = 1
    USE = 2


class FromType(Enum):
    ITER = 1


class DefUseVisitor(ast.NodeVisitor):
    def __init__(self, rda):
        self.rda = rda
        self.stack = []
        self.state = None
        self.var_name = None
        self.from_type = None

    def stash(self, new_state, var_name=None, from_type=None):
        self.stack.append((self.state, self.var_name, self.from_type))
        self.state = new_state
        self.var_name = var_name
        self.from_type = from_type

    def stash_pop(self):
        self.state, self.var_name, self.from_type = self.stack.pop()

    def resolve(self, node, new_state, var_name=None, from_type=None):
        if node is None:
            return ''
        if isinstance(node, (ast.Tuple, ast.List)):
            for elem in node.elts:
                self.resolve(elem, new_state, var_name, from_type)
            return ''
        if isinstance(node, ast.Dict):
            for value in node.values:
                self.resolve(value, new_state, var_name, from_type)
            return ''

        self.stash(new_state, var_name, from_type)
        self.visit(node)
        match self.state:
            case DefUseState.DEF:
                if self.var_name is not None and self.var_name != '_':
                    self.rda.statement_def_vars.append(self.var_name)
            case DefUseState.USE:
                if self.var_name is not None and self.var_name != '_':
                    self.rda.statement_use_vars.append(self.var_name)
                    if self.from_type == FromType.ITER:
                        self.rda.statement_use_vars.append(self.var_name + '[*]')
        var_name = self.var_name
        self.stash_pop()
        return var_name

    def resolve_call(self, node: ast.Call, from_type=None, func_name=None, var_name=None):
        get_func = False
        if func_name is None:
            func_name = self.resolve(node.func, DefUseState.USE)
        if len(self.rda.stack) < self.rda.max_stack_depth:
            if func_name is not None:
                get_func = True
                if var_name is None and '.' in func_name:
                    var_name = '.'.join(func_name.split('.')[:-1])
                func_name = func_name.split('.')[-1]
                if func_name not in self.rda.resolved_functions:
                    self.rda.resolved_functions[func_name] = 0
                if isinstance(self.rda.resolved_functions[func_name], int):
                    self.rda.resolved_functions[func_name] += 1
                    self.rda.max_stack_depth += 1
                    if self.rda.resolved_functions[func_name] >= self.rda.max_recursive_depth:
                        self.rda.max_stack_depth -= self.rda.resolved_functions[func_name]
                        return
                    self.rda.stash()
                    res = self.rda.reaching_definition_analysis(func_name)
                    self.rda.resolved_functions[func_name] = res
                    self.rda.stash_pop()
                else:
                    res = self.rda.resolved_functions[func_name]
                if res is not None:
                    if isinstance(res, list):
                        for function_name in res:
                            self.resolve_call(node, from_type, function_name, var_name)
                        return
                    call_func_args = self.rda.function_args[func_name]
                    call_func_args_redef = self.rda.function_args_redef[func_name]
                    call_func_args_use = self.rda.function_args_use[func_name]
                    self.rda.statement_call_function_args[node] = dict()
                    target_args = node.args
                    if 'self' in call_func_args:
                        if isinstance(node.func, ast.Name):
                            target_args = [ast.Name(id=var_name)] + node.args
                        elif isinstance(node.func, ast.Attribute):
                            if isinstance(node.func.value, ast.Call) and ast_comments.unparse(node.func.value.func) == 'super':
                                target_args = [ast.Name(id=var_name)] + node.args
                            else:
                                target_args = [node.func.value] + node.args
                    if 'cls' in call_func_args:
                        target_args = [ast.Name(id=func_name.split('__dot_')[-2])] + node.args
                    for i, arg in enumerate(target_args):
                        arg_name = self.resolve(arg, DefUseState.USE)
                        if arg_name is None:
                            continue
                        if call_func_args[i] in call_func_args_redef:
                            for suffix in call_func_args_redef[call_func_args[i]]:
                                self.rda.statement_def_vars.append(arg_name + suffix)
                                self.rda.statement_call_function_args[node][arg_name + suffix] = call_func_args[i] + suffix
                        if call_func_args[i] in call_func_args_use:
                            for suffix in call_func_args_use[call_func_args[i]]:
                                self.rda.statement_use_vars.append(arg_name + suffix)
                    for keyword in node.keywords:
                        keyword_name = self.resolve(keyword, DefUseState.USE)
                        if keyword_name == '':
                            continue
                        if keyword.arg in call_func_args_redef:
                            for suffix in call_func_args_redef[keyword.arg]:
                                self.rda.statement_def_vars.append(keyword_name + suffix)
                                self.rda.statement_call_function_args[node][
                                    keyword_name + suffix] = keyword.arg + suffix
                        if keyword.arg in call_func_args_use:
                            for suffix in call_func_args_use[keyword.arg]:
                                self.rda.statement_use_vars.append(keyword_name + suffix)
                    self.rda.statement_call_function_args[node]['<ret>'] = '<ret>'
                else:
                    get_func = False
        if not get_func:
            iterable = None
            for i, arg in enumerate(node.args):
                if i == 0:
                    iterable = self.resolve(arg, DefUseState.USE)
                else:
                    self.resolve(arg, DefUseState.USE)
            for keyword in node.keywords:
                if keyword.arg == 'iterable':
                    iterable = self.resolve(keyword, DefUseState.USE)
                else:
                    self.resolve(keyword, DefUseState.USE)
            if from_type == FromType.ITER and func_name == 'enumerate' and iterable:
                self.rda.statement_use_vars.append(iterable + '[*]')
            if from_type == FromType.ITER and func_name in ('items', 'values', 'keys') and iterable is None:
                self.rda.statement_use_vars.append(var_name + '[*]')
            if func_name in ('append', 'extend', 'insert', 'remove', 'pop', 'clear', 'reverse', 'update',
                             'popitem', 'add', 'discard'):
                self.rda.statement_use_vars.append(var_name + '[*]')
                self.rda.statement_def_vars.append(var_name + '[*]')
            if func_name == 'sort' and iterable:
                self.rda.statement_use_vars.append(iterable + '[*]')

    def visit_Assign(self, node):
        var_name = self.resolve(node.targets[0], DefUseState.DEF)
        self.resolve(node.value, DefUseState.USE, var_name)

    def visit_AnnAssign(self, node):
        var_name = self.resolve(node.target, DefUseState.DEF)
        self.resolve(node.value, DefUseState.USE, var_name)

    def visit_AugAssign(self, node):
        var_name = self.resolve(node.target, DefUseState.DEF)
        self.resolve(node.target, DefUseState.USE, var_name)
        self.resolve(node.value, DefUseState.USE, var_name)

    def visit_For(self, node):
        self.resolve(node.target, DefUseState.DEF)
        self.resolve(node.iter, DefUseState.USE, self.var_name, from_type=FromType.ITER)

    def visit_AsyncFor(self, node):
        var_name = self.resolve(node.target, DefUseState.DEF)
        self.resolve(node.iter, DefUseState.USE, var_name, from_type=FromType.ITER)

    def visit_FunctionDef(self, node):
        self.rda.statement_def_vars.append(node.name)

    def visit_ClassDef(self, node):
        self.rda.statement_def_vars.append(node.name)

    def visit_AsyncFunctionDef(self, node):
        self.rda.statement_def_vars.append(node.name)

    def visit_Try(self, node):
        for handler in node.handlers:
            if handler.name is not None:
                self.rda.statement_def_vars.append(handler.name)
            self.resolve(handler.type, DefUseState.USE, handler.name)

    def visit_With(self, node):
        for with_item in node.items:
            var_name = self.resolve(with_item.optional_vars, DefUseState.DEF)
            self.resolve(with_item.context_expr, DefUseState.USE, var_name)

    def visit_AsyncWith(self, node):
        for with_item in node.items:
            var_name = self.resolve(with_item.optional_vars, DefUseState.DEF)
            self.resolve(with_item.context_expr, DefUseState.USE, var_name)

    def visit_If(self, node):
        self.resolve(node.test, DefUseState.USE)

    def visit_While(self, node):
        self.resolve(node.test, DefUseState.USE)

    def visit_Assert(self, node):
        self.resolve(node.test, DefUseState.USE)

    def visit_Return(self, node):
        self.rda.statement_def_vars.append('<ret>')
        self.resolve(node.value, DefUseState.USE, '<ret>')

    def visit_Yield(self, node):
        self.rda.statement_def_vars.append('<ret>')
        self.resolve(node.value, DefUseState.USE, '<ret>')

    def visit_YieldFrom(self, node):
        self.rda.statement_def_vars.append('<ret>')
        self.resolve(node.value, DefUseState.USE, '<ret>')

    def visit_Expr(self, node):
        self.resolve(node.value, DefUseState.USE)

    def visit_Delete(self, node):
        for target in node.targets:
            self.resolve(target, DefUseState.DEF)

    def visit_Raise(self, node):
        var_name = self.resolve(node.exc, DefUseState.DEF)
        self.resolve(node.cause, DefUseState.USE, var_name)

    def visit_Name(self, node):
        self.var_name = node.id

    def visit_Constant(self, node):
        self.var_name = str(node.value)

    def visit_Attribute(self, node):
        var_name = self.resolve(node.value, DefUseState.USE)
        self.var_name = var_name + '.' + node.attr

    def visit_Subscript(self, node):
        var_name = self.resolve(node.value, DefUseState.USE)
        self.var_name = var_name + '[*]'
        self.resolve(node.slice, DefUseState.USE)

    def visit_Compare(self, node):
        self.resolve(node.left, DefUseState.USE)
        for comparator in node.comparators:
            self.resolve(comparator, DefUseState.USE)

    def visit_BinOp(self, node):
        self.resolve(node.left, DefUseState.USE)
        self.resolve(node.right, DefUseState.USE)

    def visit_BoolOp(self, node):
        for value in node.values:
            self.resolve(value, DefUseState.USE)

    def visit_UnaryOp(self, node):
        self.resolve(node.operand, DefUseState.USE)

    def visit_comprehension(self, node):
        self.resolve(node.target, DefUseState.USE)
        self.resolve(node.iter, DefUseState.USE, from_type=FromType.ITER)
        for condition in node.ifs:
            self.resolve(condition, DefUseState.USE)

    def visit_Call(self, node):
        self.resolve_call(node, from_type=self.from_type, var_name=self.var_name)
        self.var_name = ast_comments.unparse(node)
        if self.var_name is not None and self.var_name != '_':
            self.rda.statement_def_vars.append(self.var_name)


class PositionVisitor(ast.NodeVisitor):
    def __init__(self, pos):
        self.pos = pos
        self.result = None

    def generic_visit(self, node):
        if isinstance(node, ast.AST) and hasattr(node, 'lineno'):
            pos = f'{node.lineno}:{node.col_offset}-{node.end_lineno}:{node.end_col_offset}'
            if pos == self.pos:
                self.result = node
        super().generic_visit(node)


class VariableVisitor(ast.NodeVisitor):
    def __init__(self, variables_rename, module_name, init=0):
        self.variables_rename = variables_rename
        self.module_name = module_name
        self.init = init

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname is None:
                self.variables_rename[alias.name] = alias.name.replace('.', '__dot_')
            else:
                self.variables_rename[alias.asname] = alias.name.replace('.', '__dot_')

    def visit_ImportFrom(self, node):
        if node.level == 0:
            module_name = node.module.replace('.', '__dot_')
        else:
            module_name = self.module_name.split('.')
            module_name = module_name[: len(module_name) - node.level + self.init] + node.module.split('.')
            module_name = '__dot_'.join(module_name)
        for alias in node.names:
            if alias.name is not None:
                name = module_name + '__dot_' + alias.name.replace('.', '__dot_')
            else:
                name = module_name
            if alias.asname is None:
                self.variables_rename[alias.name] = name
            else:
                self.variables_rename[alias.asname] = name

    def visit_ClassDef(self, node):
        self.variables_rename[node.name] = self.module_name.replace('.', '__dot_') + '__dot_' + node.name

    def visit_FunctionDef(self, node):
        self.variables_rename[node.name] = self.module_name.replace('.', '__dot_') + '__dot_' + node.name

    def visit_AsyncFunctionDef(self, node):
        self.variables_rename[node.name] = self.module_name.replace('.', '__dot_') + '__dot_' + node.name


class RelativeVisitor(ast.NodeVisitor):
    def __init__(self, relative_name: set):
        self.relative_name = relative_name

    def visit_ClassDef(self, node):
        if '__dot_' in node.name:
            self.relative_name.add(node.name)
        for base in node.bases:
            self.visit(base)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for body in node.body:
            if isinstance(body, ast.FunctionDef) and isinstance(body.body[0], ast.Pass):
                # func_name = body.name.split('__dot_')[-1]
                # if func_name.startswith('__') and func_name.endswith('__'):
                #     self.visit(body)
                self.visit(body)

    def visit_FunctionDef(self, node):
        if '__dot_' in node.name:
            self.relative_name.add(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)

        for body in node.body:
            self.visit(body)

    def visit_AsyncFunctionDef(self, node):
        if '__dot_' in node.name:
            self.relative_name.add(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for body in node.body:
            self.visit(body)

    def visit_Name(self, node):
        if '__dot_' in node.id:
            self.relative_name.add(node.id)

    def visit_Attribute(self, node):
        if '__dot_' in node.attr:
            self.relative_name.add(node.attr)
        self.visit(node.value)

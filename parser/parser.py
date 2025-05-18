import lark
from flask import current_app
from db import get_db

getvar_cb = None

def process_page(text: str, variable_getter) -> str:
    """
    Evaluates all expressions in text and returns HTML
    Args: Text to process, user id to get variables from
    Returns: HTML code of a processed page
    """
    global getvar_cb
    getvar_cb = variable_getter
    processed = ""
    root = parse(text)
    for node in root.children:
        processed += process(node)

    return processed

def load_grammar() -> str:
    """
    Loads grammar file and returns it's contents
    """
    grammar_path = current_app.config['GRAMMAR_PATH']
    with open(grammar_path) as f:
        grammar = f.read()
    return grammar

def parse(text: str) -> lark.tree.Tree:
    """
    Parses given code to parse tree
    Args: Text to parse
    Returns: Root node of parse tree
    """
    parser = lark.Lark(load_grammar())
    return parser.parse(text)

def process(node: lark.tree.Tree) -> str:
    """
    Processes one top-level node and returns it's html
    """
    match node.data:
        case "text":
            return str(node.children[0])
        case "subst":
            return eval_subst(node)
        case "if":
            return eval_if(node)
        case "link":
            return parse_link(node)
    raise UnknownNode(node.data)

def eval_if(node: lark.tree.Tree) -> str:
    """
    Evaluates 'if' block
    """
    if node.data != "if":
        raise ValueError

    ret = ""
    if comp_eval(node.children[0]):
        for nd in node.children[1].children:
            ret += process(nd)
        return ret

    for nd in node.children[2:]:
        if nd.data == "elif" and comp_eval(nd.children[0]):
            for n in nd.children[1:]:
                ret += process(n)
            return ret
        elif nd.data == "else":
            for n in nd.children:
                ret += process(n)
            return ret
    return ""


def eval_expr(node: lark.tree.Tree) -> int:
    """
    Evaluates expression and returns it's result as int.

    Returns: int
    Throws: VariableNotSetError if at least one variable is not set
    """
    match node.data:
        case "expr":
            return eval_expr(node.children[0])
        case "sum":
            return eval_expr(node.children[0]) + eval_expr(node.children[1])
        case "diff":
            return eval_expr(node.children[0]) - eval_expr(node.children[1])
        case "mult":
            return eval_expr(node.children[0]) * eval_expr(node.children[1])
        case "div":
            return eval_expr(node.children[0]) // eval_expr(node.children[1])
        case "number":
            return int(str(node.children[0]))
        case "neg":
            return -eval_expr(node.children[0])
        case "var":
            varname = str(node.children[0])
            try:
                return int(getvar(varname))
            except KeyError as e:
                raise VariableNotSetError(varname) from e
    raise UnknownNode(node.data)

def eval_subst(node: lark.tree.Tree) -> str:
    """
    Does expression substitution, evauating expr inside
    and returning default value is eval_expr failed
    """
    try:
        return str(eval_expr(node.children[0]))
    except VariableNotSetError:
        if len(node.children) > 1:
            return str(node.children[1])
        return ""  # maybe raise so eval_expr could insert some error code?

def parse_link(node: lark.tree.Tree) -> str:
    """Turns parse tree node to link html code"""
    text = process(node.children[0])
    link = str(node.children[1])
    if len(node.children) > 2:
        vars = []
        for nd in node.children[2].children:
            match nd.data:
                case "flag":
                    vars.append(str(nd.children[0]) + "=true")
                case "unflag":
                    vars.append(str(nd.children[0]) + "=")
                case "set":
                    vars.append(str(nd.children[0]) + "=" + str(eval_expr(nd.children[1])))
        link += "?" + "&".join(vars)
    return f'<a href="{link}">{text}</a>'

def comp_eval(node: lark.tree.Tree) -> bool:
    """
    Evaluates predicate set by parse tree node into bool

    Returns: bool
    Throws: UnknownComparator if comparator in comp expression is invalid
    """
    match node.data:
        case "flagvar":
            try:
                ret = bool(getvar(str(node.children[0])))
            except KeyError:
                ret = False
            return ret
        case "comp":
            try:
                lhs = eval_expr(node.children[0])
                rhs = eval_expr(node.children[2])
            except VariableNotSetError:
                return False

            comp = str(node.children[1])
            match comp:
                case "<":
                    return lhs < rhs
                case ">":
                    return lhs > rhs
                case "<=":
                    return lhs <= rhs
                case ">=":
                    return lhs >= lhs
                case "=":
                    return lhs == rhs
            raise UnknownComparator(comp)
        case "or":
            return comp_eval(node.children[0]) or comp_eval(node.children[1])
        case "and":
            return comp_eval(node.children[0]) and comp_eval(node.children[1])
    raise UnknownNode(node.data)

def getvar(name: str) -> str:
    """
    Gets variable value from database. If value is not present — throws.

    Returns: Requested variable value
    Throws: KeyError if asked variable is not set
    """
    return getvar_cb(name)

class UnknownComparator(Exception):
    """
    Raised when comparator in comp expression is unknown.
    Does not expected to be raised under normal circumstances
    """
    def __init__(self, msg=""):
        self.message = msg

class UnknownNode(Exception):
    """
    Raised when node name is not matched.
    Does not expected to be raised under normal circumstances
    """
    def __init__(self, msg):
        self.message = msg

class VariableNotSetError(Exception):
    """
    Raised when there is an unset variable in eval_expr
    """
    def __init__(self, msg):
        self.message = msg

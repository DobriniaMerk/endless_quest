import lark
from flask import current_app
from urllib.parse import urlencode
from enum import Enum

GETVAR_CB = None
GRAMMAR = None


class Vartype(Enum):
    ANY=1
    STRING=1
    INT=2
    BOOL=3


def process_page(text: str, variable_getter) -> str:
    """
    Evaluates all expressions in text and returns HTML
    Args: Text to process, callback to get variables from
    Returns: HTML code of a processed page
    """
    global GETVAR_CB
    GETVAR_CB = variable_getter
    processed = ""
    try:
        root = parse(text)
    except Exception as e:
        return str(e)
    for node in root.children:
        processed += process(node)

    return processed


def load_grammar() -> str:
    """
    Loads grammar file and returns it's contents
    """
    global GRAMMAR
    if GRAMMAR is not None:
        return GRAMMAR

    grammar_path = current_app.config["GRAMMAR_PATH"]
    with open(grammar_path, encoding="utf-8") as f:
        GRAMMAR = f.read()
    return GRAMMAR


def parse(text: str) -> lark.tree.Tree:
    """
    Parses given code to parse tree
    Args: Text to parse

    Throws: Inherited from ParserError if syntax is incorrect.
    Returns: Root node of parse tree

    """
    parser = lark.Lark(load_grammar())
    try:
        return parser.parse(text)
    except lark.UnexpectedInput as u:
        exc = u.match_examples(parser.parse, {
            MissingDestination: ["((exmpl;))",
                                 "((exmpl))"],
            UnclosedBlock: ["((example; 1",
                            "((t;1))((+flag",
                            # "(?"
                            "(?flag",
                            # "(?flag?) (!",
                            "(?flag?) (!flag",
                            # "(%",
                            "(%var",],
            EmptyVarblock: ["((exmpl; 1))(())"]
        }, use_accepts=True)

        if not exc:
            raise
        raise exc(u.get_context(text), u.line, u.column) from u



def process(node: lark.tree.Tree) -> str:
    """
    Processes one top-level node and returns it's html

    Throws: Exceptions inherited from MarkdownError. Should be catched and displayed instead of text.
    Returns: Resulting html after markdown evaluation.
    """
    try:
        match node.data:
            case "text":
                ret = str(node.children[0])
                return ret
            case "newline":
                return str(node.children[0])
            case "subst":
                return eval_subst(node)
            case "if":
                return eval_if(node)
            case "link":
                return parse_link(node)
        raise UnknownNode("Unknow node: " + node.data + ". This is a site error, please report to developers.")
    except MarkdownError as e:
        return '<p style="color: red>"' + str(e) + '</p>'


def eval_if(node: lark.tree.Tree) -> str:
    """
    Evaluates 'if' block
    """
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
        if nd.data == "else":
            for n in nd.children:
                ret += process(n)
            return ret
    return ""


def eval_expr(node: lark.tree.Tree, expected_type: Vartype = Vartype.ANY) -> str | int | bool:
    """
    Evaluates expression and returns it's result as expected_type requires.

    Returns: str
    Throws: VariableError if encountered variable problems inside.
    """
    match node.data:
        case "expr":
            ret = eval_expr(node.children[0])
        case "string":
            ret = str(node.children[0])[1:-1]
        case "sum":
            ret = eval_expr(node.children[0], Vartype.INT) + eval_expr(node.children[1], Vartype.INT)
        case "diff":
            ret = eval_expr(node.children[0], Vartype.INT) - eval_expr(node.children[1], Vartype.INT)
        case "mult":
            ret = eval_expr(node.children[0], Vartype.INT) * eval_expr(node.children[1], Vartype.INT)
        case "div":
            ret = eval_expr(node.children[0], Vartype.INT) // eval_expr(node.children[1], Vartype.INT)
        case "number":
            ret = int(str(node.children[0]))
        case "neg":
            ret = -eval_expr(node.children[0], Vartype.INT)
        case "var":
            varname = str(node.children[0])
            try:
                ret = getvar(varname)
            except VariableNotSetError:
                if expected_type == Vartype.STRING:
                    return ""
                elif expected_type == Vartype.INT:
                    return 0
                elif expected_type == Vartype.BOOL:
                    return False
        case _:
            raise UnknownNode(node.data)

    if expected_type == Vartype.STRING:
        return str(ret)
    elif expected_type == Vartype.BOOL:
        return bool(ret)
    elif expected_type == Vartype.INT:
        try:
            return int(ret)
        except ValueError as e:
            raise VariableError(f"{ret} is not a number") from e


def eval_subst(node: lark.tree.Tree) -> str:
    """
    Does expression substitution, evauating expr inside
    and returning default value is eval_expr failed
    """
    return eval_expr(node.children[0], Vartype.STRING)


def parse_link(node: lark.tree.Tree) -> str:
    """Turns parse tree node to link html code"""
    text = process(node.children[0])
    variables = {}
    if len(node.children) > 2:
        for nd in node.children[2].children:
            match nd.data:
                case "flag":
                    variables[str(nd.children[0])] = "true"
                case "unflag":
                    variables[str(nd.children[0])] = ""
                case "set":
                    variables[str(nd.children[0])] = eval_expr(nd.children[1], Vartype.STRING)
    return f'<a href="{str(node.children[1])}?{urlencode(variables)}">{text}</a>'


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
            except VariableNotSetError:
                ret = False
            return ret
        case "comp":
            lhs = eval_expr(node.children[0], Vartype.INT)
            rhs = eval_expr(node.children[2], Vartype.INT)

            comp = str(node.children[1])
            match comp:
                case "<":
                    return lhs < rhs
                case ">":
                    return lhs > rhs
                case "<=":
                    return lhs <= rhs
                case ">=":
                    return lhs >= rhs
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
    Returns: Requested variable value
    Throws: VariableNotSetError if variable is not set
    """
    try:
        return GETVAR_CB(name)
    except Exception:
        raise VariableNotSetError(name + " is not set")


class UnknownComparator(Exception):
    """
    Raised when comparator in comp expression is unknown.
    Does not expected to be raised under normal circumstances
    """

    def __init__(self, msg=""):
        self.message = msg


class MarkdownError(Exception):
    """
    Error while evaluating or parsing markdown. Should be
    intercepted and printed instead paragraph's text.

    """
    pass


class UnknownNode(MarkdownError):
    """
    Raised when node name is not matched.
    Does not expected to be raised under normal circumstances
    """
    pass

class VariableNotSetError(MarkdownError):
    """
    Raised when there is an unset variable in eval_expr
    """
    pass

class VariableError(MarkdownError):
    """
    Something wrong with variables.
    """
    pass

class MarkdownSyntaxError(MarkdownError):
    """
    Raised when parser encountered something wrong.
    """
    pass


class ParserError(Exception):
    label = ""
    def __str__(self):
        context, line, column = self.args
        return f"{self.label} encountered at line {line}.\n\n{context}"

class UnclosedBlock(ParserError):
    label = "Unclosed control block"

class MissingDestination(ParserError):
    label = "Link without destination paragraph number"

# class NonexistentOperation(ParserError):
#     label = "Operation that does not exist"

class EmptyVarblock(ParserError):
    label = "Empty variable assignment block"

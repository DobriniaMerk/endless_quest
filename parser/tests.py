import unittest
from unittest.mock import patch
from parser import process_page, parse, eval_if, eval_expr,parse_link, comp_eval

class TestTemplateProcessor(unittest.TestCase):
    @patch('parser.getvar')
    def test_process_page_simple_text(self, mock_getvar):
        result = process_page("Hello world")
        self.assertEqual(result, "Hello world")

    @patch('parser.getvar')
    def test_process_page_simple_subst(self, mock_getvar):
        mock_getvar.return_value = "5"
        result = process_page("[x]")
        self.assertEqual(result, "5")

    @patch('parser.getvar')
    def test_process_page_subst_with_default(self, mock_getvar):
        mock_getvar.side_effect = KeyError("x")
        result = process_page("[x|10]")
        self.assertEqual(result, "10")

    @patch('parser.getvar')
    def test_eval_expr_simple(self, mock_getvar):
        mock_getvar.return_value = "5"
        tree = parse("[x + 3]")
        result = eval_expr(tree.children[0].children[0])
        self.assertEqual(result, 8)

    @patch('parser.getvar')
    def test_eval_expr_complex(self, mock_getvar):
        mock_getvar.side_effect = lambda x: {"a": "5", "b": "2"}[x]
        tree = parse("[(a * b) + 10 / 2]")
        result = eval_expr(tree.children[0].children[0])
        self.assertEqual(result, 15)

    @patch('parser.getvar')
    def test_eval_expr_negation(self, mock_getvar):
        mock_getvar.return_value = "5"
        tree = parse("[-x]")
        result = eval_expr(tree.children[0].children[0])
        self.assertEqual(result, -5)

    @patch('parser.getvar')
    def test_comp_eval_flagvar_true(self, mock_getvar):
        mock_getvar.return_value = "true"
        tree = parse("::x::Show&&")
        result = comp_eval(tree.children[0].children[0])
        self.assertTrue(result)

    @patch('parser.getvar')
    def test_comp_eval_flagvar_false(self, mock_getvar):
        mock_getvar.side_effect = KeyError("x")
        tree = parse("::x::Show&&")
        result = comp_eval(tree.children[0].children[0])
        self.assertFalse(result)

    @patch('parser.getvar')
    def test_comp_eval_comparison(self, mock_getvar):
        mock_getvar.return_value = "5"
        tree = parse("::x > 3::Show&&")
        result = comp_eval(tree.children[0].children[0])
        self.assertTrue(result)

    @patch('parser.getvar')
    def test_comp_eval_logical_ops(self, mock_getvar):
        mock_getvar.side_effect = lambda x: {"a": "5", "b": "10"}[x]
        tree = parse("::a > 3 & b < 15::Show&&")
        result = comp_eval(tree.children[0].children[0])
        self.assertTrue(result)

    @patch('parser.getvar')
    def test_eval_if_simple(self, mock_getvar):
        mock_getvar.return_value = "1984"
        tree = parse("::x::Show this&&")
        result = eval_if(tree.children[0])
        self.assertEqual(result, "Show this")

    @patch('parser.getvar')
    def test_eval_if_elif(self, mock_getvar):
        mock_getvar.side_effect = lambda x: {"b": "true"}.get(x)
        tree = parse("::a::First%a%Second%b%Third%%Default&&")
        result = eval_if(tree.children[0])
        self.assertEqual(result, "Third")

    @patch('parser.getvar')
    def test_eval_if_else(self, mock_getvar):
        mock_getvar.return_value = ""
        tree = parse("::x::First%%Default&&")
        result = eval_if(tree.children[0])
        self.assertEqual(result, "Default")

    @patch('parser.getvar')
    def test_parse_link_simple(self, mock_getvar):
        tree = parse("{Text|123}")
        result = parse_link(tree.children[0])
        self.assertEqual(result, '<a href="123">Text</a>')

    @patch('parser.getvar')
    def test_parse_link_with_params(self, mock_getvar):
        mock_getvar.side_effect = lambda x: {"y": "5"}[x]
        tree = parse("{Text|123}{+a,-b,x=2*y,y=3}")
        result = parse_link(tree.children[0])
        self.assertEqual(result, '<a href="123?a=true&b=&x=10&y=3">Text</a>')

if __name__ == '__main__':
    unittest.main()

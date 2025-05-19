import subprocess, ast

def get_docstring_lines(path: str) -> set[int]:
    """Возвращает номера строк, покрытые модульными/функц/класс-докстрингами."""
    text = open(path, encoding='utf-8').read()
    tree = ast.parse(text)
    doc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc and hasattr(node, 'body') and node.body:
                first = node.body[0]
                # Для py>=3.8 есть атрибуты .lineno и .end_lineno
                start = getattr(first, 'lineno', None)
                end   = getattr(first, 'end_lineno', start)
                if start and end:
                    doc_lines.update(range(start, end+1))
    return doc_lines

def blame_file(path: str, doc_lines: set[int], totals: dict):
    """Добавляет в totals[автор] по 1 за каждую «реальную» строку кода."""
    p = subprocess.run(
        ['git', 'blame', '--line-porcelain', path],
        stdout=subprocess.PIPE, text=True
    )
    author = None
    lineno = 0
    for line in p.stdout.splitlines():
        if line.startswith('author '):
            author = line[len('author '):]
        elif line.startswith('\t'):  # контент строки
            lineno += 1
            content = line[1:]
            if (not content.strip()             # пустая
                or lineno in doc_lines          # docstring
                or content.lstrip().startswith('#')  # комментарий
                or content.lstrip().startswith('from')  # комментарий
                or content.lstrip().startswith('import')):  # комментарий
                continue
            totals[author] = totals.get(author, 0) + 1

def main():
    totals: dict[str,int] = {}
    # список всех .py-файлов в repo
    files = subprocess.run(['git', 'ls-files', '*.py'],
                           stdout=subprocess.PIPE, text=True).stdout.split()
    for f in files:
        doc = get_docstring_lines(f)
        blame_file(f, doc, totals)
    # вывод
    for author, cnt in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        print(f"{author:25s}: {cnt}")

if __name__ == '__main__':
    main()


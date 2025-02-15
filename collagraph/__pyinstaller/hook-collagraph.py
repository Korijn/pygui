import ast
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

from collagraph.sfc.compiler import get_script_ast
from collagraph.sfc.parser import CGXParser


def hook(hook_api):
    collagraph_uses = hook_api.analysis.graph.get_code_using("collagraph")

    hidden_imports = set()
    datas = []
    for package, code in collagraph_uses.items():
        filename = Path(code.co_filename)
        hidden_imports |= collect_hidden_imports(filename.parent)
        datas += collect_data_files(package, includes=["**/*.cgx"])

    hook_api.add_imports(*hidden_imports)
    hook_api.add_datas(datas)


def collect_hidden_imports(folder):
    folder = Path(folder)

    hidden_imports = set()
    for path in folder.glob("**/*.cgx"):
        template = path.read_text()
        # Parse the file component into a tree of Node instances
        parser = CGXParser()
        parser.feed(template)

        # Get the AST from the script tag
        script_tree = get_script_ast(parser, path)

        # Find a list of imported names (or aliases, if any)
        # Those names don't have to be wrapped by `_lookup`
        imported_names = ImportsCollector()
        imported_names.visit(script_tree)

        hidden_imports |= imported_names.names

    return hidden_imports


class ImportsCollector(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_ImportFrom(self, node):  # noqa: N802
        for alias in node.names:
            self.names.add(".".join([node.module, alias.name]))
        self.names.add(node.module)

    def visit_Import(self, node):  # noqa: N802
        for alias in node.names:
            self.names.add(alias.name)

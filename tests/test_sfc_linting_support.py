import ast
from pathlib import Path

from collagraph.sfc import compiler

DATA_PATH = Path(__file__).parent / "data"


def test_cgx_construct_ast():
    tree, name = compiler.construct_ast(DATA_PATH / "simple.cgx")

    assert name == "Simple"
    assert isinstance(tree, ast.Module)
    import_collagraph, class_def = tree.body
    assert class_def.name == "Simple"

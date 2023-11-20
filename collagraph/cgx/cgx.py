import ast
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import textwrap

from collagraph import Component


# Adjust this setting to disable some runtime checks
# Defaults to True, except when it is part of an installed application
CGX_RUNTIME_WARNINGS = not getattr(sys, "frozen", False)

SUFFIX = "cgx"
DIRECTIVE_PREFIX = "v-"
DIRECTIVE_BIND = f"{DIRECTIVE_PREFIX}bind"
DIRECTIVE_IF = f"{DIRECTIVE_PREFIX}if"
DIRECTIVE_ELSE_IF = f"{DIRECTIVE_PREFIX}else-if"
DIRECTIVE_ELSE = f"{DIRECTIVE_PREFIX}else"
CONTROL_FLOW_DIRECTIVES = (DIRECTIVE_IF, DIRECTIVE_ELSE_IF, DIRECTIVE_ELSE)
DIRECTIVE_FOR = f"{DIRECTIVE_PREFIX}for"
DIRECTIVE_ON = f"{DIRECTIVE_PREFIX}on"
AST_GEN_VARIABLE_PREFIX = "_ast_"

COMPONENT_CLASS_DEFINITION = re.compile(r"class\s*(.*?)\s*\(.*?\)\s*:")
MOUSTACHES = re.compile(r"\{\{.*?\}\}")


def load(path):
    """
    Loads and returns a component from a CGX file.

    A subclass of Component will be created from the CGX file
    where the contents of the <template> tag will be used as
    the `render` function, while the contents of the <script>
    tag will be used to provide the rest of the functions of
    the component.

    For example:

        <template>
          <item foo="bar">
            <item baz="bla"/>
          </item>
        </template

        <script>
        import collagraph as cg

        class Foo(cg.Component):
            pass
        </script>

    """
    template = path.read_text()

    return load_from_string(template, path)


def load_from_string(template, path=None):
    """
    Load template from a string
    """
    if path is None:
        path = "<template>"
        template = textwrap.dedent(template)

    # Construct the AST tree
    tree, name = construct_ast(path=path, template=template)

    # Compile the tree into a code object (module)
    code = compile(tree, filename=str(path), mode="exec")
    # Execute the code as module and pass a dictionary that will capture
    # the global and local scope of the module
    module_namespace = {}
    exec(code, module_namespace)

    # Check that the class definition is an actual subclass of Component
    component_class = module_namespace[name]
    if not issubclass(component_class, Component):
        raise ValueError(
            f"The last class defined in {path} is not a subclass of "
            f"Component: {component_class}"
        )
    return component_class, module_namespace


def construct_ast(path, template=None):
    """
    Returns a tuple of the constructed AST tree and name of (enhanced) component class.

    Construct an AST from the CGX file by first creating an AST from the script tag,
    and then compile the contents of the template tag and insert that into the component
    class definition as `render` function.
    """
    if not template:
        template = Path(path).read_text()

    # Parse the file component into a tree of Node instances
    parser = CGXParser()
    parser.feed(template)

    # Get the AST from the script tag
    script_tree = get_script_ast(parser, path)

    # Find a list of imported names (or aliases, if any)
    # Those names don't have to be wrapped by `_lookup`
    imported_names = ImportsCollector()
    imported_names.visit(script_tree)

    # Find the last ClassDef and assume that it is the
    # component that is defined in the SFC
    component_def = None
    for node in reversed(script_tree.body):
        if isinstance(node, ast.ClassDef):
            component_def = node
            break

    # Create render function as AST and inject into the ClassDef
    template_node = parser.root.child_with_tag("template")
    if len(template_node.children) != 1:
        raise ValueError(
            "There should be precisely one root element defined in "
            f"the template. Found {len(template_node.children)}."
        )
    render_tree = create_ast_render_function(
        template_node.children[0], names=imported_names.names
    )
    ast.fix_missing_locations(render_tree)

    # Put location of render function outside of the script tag
    # This makes sure that the render function can be excluded
    # from linting.
    # Note that it's still possible to put code after the component
    # class at the end of the script node.
    script_node = parser.root.child_with_tag("script")
    line, _ = script_node.end
    ast.increment_lineno(render_tree, n=line)
    component_def.body.append(render_tree)

    # Because we modified the AST significantly we need to call an AST
    # method to fix any `lineno` and `col_offset` attributes of the nodes
    ast.fix_missing_locations(script_tree)
    return script_tree, component_def.name


def get_script_ast(parser, path):
    """
    Returns the AST created from the script tag in the CGX file.
    """
    # Read the data from script block
    script_node = parser.root.child_with_tag("script")
    script = script_node.data
    line, _ = script_node.location

    # Create an AST from the script
    script_tree = ast.parse(script, filename=str(path), mode="exec")
    # Make sure that the lineno's match up with the lines in the CGX file
    ast.increment_lineno(script_tree, n=line)
    return script_tree


def create_ast_render_function(node, names):
    """
    Create render function as AST.
    """
    extra_statements = [
        ast.ImportFrom(
            module="collagraph",
            names=[ast.alias(name="create_element", asname="_create_element")],
            level=0,
        )
    ]
    if CGX_RUNTIME_WARNINGS:
        names_str = ", ".join([f"'{name}'" for name in names])
        code = textwrap.dedent(
            f"""
            from warnings import warn as _warn

            for name in {{{names_str}}}:
                if name in self.state:
                    _warn(
                        f"Found imported name '{{name}}' "
                        f"as key in self.state: {{self}}.\\n"
                        "If the value from self.state is intended, please resolve by "
                        f"replacing '{{name}}' with 'state['{{name}}']'"
                    )
                if name in self.props:
                    _warn(
                        f"Found imported name '{{name}}' "
                        f"as key in self.props: {{self}}.\\n"
                        "If the value from self.props is intended, please resolve by "
                        f"replacing '{{name}}' with 'props['{{name}}']'"
                    )
                if hasattr(self, name):
                    _warn(
                        f"Found imported name '{{name}}' "
                        f"as attribute on self: {{self}}.\\n"
                        "If the attribute from self is intended, please resolve by "
                        f"replacing '{{name}}' with 'self.{{name}}'"
                    )
            """
        )
        check_names = ast.parse(code)
        extra_statements.extend(check_names.body)

    return ast.FunctionDef(
        name="render",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg("self")],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[
            *extra_statements,
            ast.Return(value=call_create_element(node, names=names)),
        ],
        decorator_list=[],
    )


def call_create_element(node, *, names):
    """
    Returns an ast.Call of `collagraph.create_element()` with the right args
    for the given node.

    Names is a set of variable names that should not be wrapped in
    the _lookup method.
    """
    return ast.Call(
        func=ast.Name(id="_create_element", ctx=ast.Load()),
        args=convert_node_to_args(node, names=names),
        keywords=[],
    )


def call_render_slot(node, *, names=None):
    slot_name = node.attrs.get("name", "default")

    return ast.Starred(
        value=ast.IfExp(
            # Check whether the slot name is present in
            # the _slots property of the component
            test=ast.Compare(
                left=ast.Constant(value=slot_name),
                ops=[ast.In()],
                comparators=[
                    ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr="_slots",
                        ctx=ast.Load(),
                    )
                ],
            ),
            # If so, then we'll call render_slot
            body=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="self", ctx=ast.Load()),
                    attr="render_slot",
                    ctx=ast.Load(),
                ),
                args=[ast.Constant(value=slot_name)],
                keywords=[],
            ),
            # Otherwise, we render the fallback content
            orelse=ast.List(
                elts=[call_create_element(node, names=names)],
                ctx=ast.Load(),
            ),
        ),
        ctx=ast.Load(),
    )


def convert_node_to_args(node, *, names=None):
    """
    Converts the node to args that can be passed to `collagraph.create_element()`.
    """
    # Construct the first argument: type of node
    if not node.tag[0].islower():
        # If the tag does not start with a capital, then it is assumed to be
        # a class or function, so a Name node is inserted in the ast tree
        type_arg = ast.Name(id=node.tag, ctx=ast.Load())
    elif "." in node.tag:
        # If a dot is found in the tag, then it is assumed that the tag represents
        # a package/module attribute lookup
        name, *attributes = node.tag.split(".")
        result = ast.Name(id=name, ctx=ast.Load())
        for attr in attributes:
            result = ast.Attribute(value=result, attr=attr, ctx=ast.Load())
        type_arg = result
    else:
        # Otherwise it is just a constant string
        type_arg = ast.Constant(value=node.tag)

    # Construct the second argument: the props (dict) for the node
    props_keys = []
    props_values = []

    for key, val in node.attrs.items():
        # All non-directive attributes can be constructed easily
        if not is_directive(key):
            props_keys.append(ast.Constant(value=key))
            props_values.append(ast.Constant(value=val))
            continue

        if key.startswith((DIRECTIVE_BIND, ":")):
            if key == DIRECTIVE_BIND:
                # Use 'None' to mark this is a binding of multiple attributes
                props_keys.append(None)
                props_values.append(
                    RewriteName(skip=names).visit(ast.parse(val, mode="eval")).body
                )
            else:
                _, key = key.split(":")
                props_keys.append(ast.Constant(value=key))
                props_values.append(
                    RewriteName(skip=names).visit(ast.parse(val, mode="eval")).body
                )
            continue

        if key.startswith((DIRECTIVE_ON, "@")):
            split_char = "@" if key.startswith("@") else ":"
            _, key = key.split(split_char)
            key = f"on_{key}"
            props_keys.append(ast.Constant(value=key))

            tree = ast.parse(val, mode="eval")
            # v-on directives allow for lambdas which define arguments
            # which need to be skipped by the RewriteName visitor
            lambda_names = LambdaNamesCollector()
            lambda_names.visit(tree)
            RewriteName(skip=names | lambda_names.names).visit(tree)
            props_values.append(tree.body)
            continue

        if key.startswith((DIRECTIVE_FOR)):
            # Skip right away, parent should've already handled this
            continue

    # Construct the other arguments: the children of the node
    children_args = []

    slots = {}
    control_flow = []
    for child in node.children:
        directive = None

        # Handle for-directives
        if for_expression := child.attrs.get(DIRECTIVE_FOR):
            for_expression = f"[None for {for_expression}]"
            for_tree = ast.parse(for_expression, mode="eval").body

            # Find the names that are defined as part of the comprehension(s)
            # E.g: 'i, (a, b) in enumerate(some_collection)' defines the names
            # i, a and b, so we don't want to wrap those names with `_lookup()`
            name_collector = NameCollector()
            for generator in for_tree.generators:
                # Apparently, a node visitor does _not_ visit the root node...
                # So instead, just add the name directly if the root is an ast.Name node
                if isinstance(generator.target, ast.Name):
                    name_collector.names.add(generator.target.id)
                else:
                    name_collector.generic_visit(generator.target)

            local_names = names.union(name_collector.names)
            RewriteName(skip=local_names).visit(for_tree)

            for_tree.elt = call_create_element(child, names=local_names)

            result = ast.Starred(value=for_tree, ctx=ast.Load())
            children_args.append(result)
            continue

        # Handle control flow directives
        if directive := child.control_flow():
            if directive == "v-if" and control_flow:
                children_args.append(create_control_flow_ast(control_flow, names=names))
                control_flow = []
            control_flow.append((directive, child))

        # Gather all the non-template children within a component tag and
        # treat them as the content for the default slot
        if node.tag[0].isupper() or "." in node.tag:
            default_slot_content = [
                child for child in node.children if child.tag != "template"
            ]

            if default_slot_content:
                virtual_template_node = Node("template")
                virtual_template_node.children = default_slot_content
                slots["default"] = virtual_template_node

        for attr in child.attrs.keys():
            if attr.startswith(("v-slot", "#")):
                slot_name = attr.split(":")[-1].split("#")[-1]
                if slot_name == "v-slot":
                    slot_name = "default"
                slots[slot_name] = child

        if not directive:
            if control_flow:
                children_args.append(create_control_flow_ast(control_flow, names=names))
                control_flow = []
            if child.tag == "slot":
                children_args.append(call_render_slot(child, names=names))
            else:
                children_args.append(call_create_element(child, names=names))

    if control_flow:
        children_args.append(create_control_flow_ast(control_flow, names=names))
        control_flow = []

    if node.data:
        groups = [match for match in MOUSTACHES.finditer(node.data)]
        if not groups:
            children_args.append(ast.Constant(value=node.data))
        else:
            offset = 0
            string_parts = []
            expressions = []
            for group in groups:
                span = group.span()
                string_parts.append(ast.Constant(value=node.data[offset : span[0]]))
                expr = (node.data[span[0] + 2 : span[1] - 2]).strip()
                expressions.append(
                    RewriteName(skip=names).visit(ast.parse(expr, mode="eval")).body
                )
                offset = span[1]

            string_suffix = ast.Constant(value=node.data[offset:])

            children_args.append(
                # The following tree is the ast of the following expression:
                # "".join(
                #     [x + str(y) for x, y in zip(string_parts, expressions)]
                #     + [string_suffix]
                # )
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Constant(value=""), attr="join", ctx=ast.Load()
                    ),
                    args=[
                        ast.BinOp(
                            left=ast.ListComp(
                                elt=ast.BinOp(
                                    left=ast.Name(id="x", ctx=ast.Load()),
                                    op=ast.Add(),
                                    right=ast.Call(
                                        func=ast.Name(id="str", ctx=ast.Load()),
                                        args=[ast.Name(id="y", ctx=ast.Load())],
                                        keywords=[],
                                    ),
                                ),
                                generators=[
                                    ast.comprehension(
                                        target=ast.Tuple(
                                            elts=[
                                                ast.Name(id="x", ctx=ast.Store()),
                                                ast.Name(id="y", ctx=ast.Store()),
                                            ],
                                            ctx=ast.Store(),
                                        ),
                                        iter=ast.Call(
                                            func=ast.Name(id="zip", ctx=ast.Load()),
                                            args=[
                                                ast.List(
                                                    elts=string_parts, ctx=ast.Load()
                                                ),
                                                ast.List(
                                                    elts=expressions, ctx=ast.Load()
                                                ),
                                            ],
                                            keywords=[],
                                        ),
                                        ifs=[],
                                        is_async=0,
                                    )
                                ],
                            ),
                            op=ast.Add(),
                            right=ast.List(elts=[string_suffix], ctx=ast.Load()),
                        )
                    ],
                    keywords=[],
                )
            )

    # Create a starred list comprehension that when called, will generate
    # all child elements
    starred_expr = ast.Starred(
        value=ast.ListComp(
            elt=ast.Name(
                id=f"{AST_GEN_VARIABLE_PREFIX}child",
                ctx=ast.Load(),
            ),
            generators=[
                ast.comprehension(
                    target=ast.Name(
                        id=f"{AST_GEN_VARIABLE_PREFIX}child",
                        ctx=ast.Store(),
                    ),
                    iter=ast.List(
                        elts=children_args,
                        ctx=ast.Load(),
                    ),
                    ifs=[
                        # Filter out all None elements
                        ast.Compare(
                            left=ast.Name(
                                id=f"{AST_GEN_VARIABLE_PREFIX}child",
                                ctx=ast.Load(),
                            ),
                            ops=[ast.IsNot()],
                            comparators=[ast.Constant(value=None)],
                        )
                    ],
                    is_async=0,
                )
            ],
        ),
        ctx=ast.Load(),
    )
    if slots:
        starred_expr = ast.Dict(
            keys=[ast.Constant(value=key) for key in slots.keys()],
            values=[
                ast.Lambda(
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="props")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=call_create_element(val, names=names),
                )
                for val in slots.values()
            ],
        )

    # Process all (bound) attrs in order. The last defined attr will prevail.
    pre_multiple_bind = ast.Dict(keys=[], values=[])
    multiple_bind = None
    post_multiple_bind = ast.Dict(keys=[], values=[])

    curr_dict = pre_multiple_bind
    for key, val in zip(props_keys, props_values):
        # When key is None, it is a multiple binding
        if key is None:
            # And in that case the parsed expression can be used directly
            multiple_bind = val
            curr_dict = post_multiple_bind
            continue

        curr_dict.keys.append(key)
        curr_dict.values.append(val)

    # Build an expresion based on the collected values
    # In most complex situation results in:
    #   pre_multiple_kind | multiple_bind | post_multiple_bind
    attr_expression = pre_multiple_bind
    if multiple_bind is not None:
        if not pre_multiple_bind.keys:
            attr_expression = multiple_bind
        else:
            attr_expression = ast.BinOp(
                left=pre_multiple_bind,
                op=ast.BitOr(),
                right=multiple_bind,
            )
    if post_multiple_bind.keys:
        attr_expression = ast.BinOp(
            left=attr_expression,
            op=ast.BitOr(),
            right=post_multiple_bind,
        )

    # Return all the arguments
    if not slots and not children_args:
        return [type_arg, attr_expression]
    return [type_arg, attr_expression, starred_expr]


def create_control_flow_ast(control_flow, *, names):
    """
    Create an AST of control flow nodes (if/else-if/else)
    """
    (if_directive, if_node), *if_else_statements = control_flow
    # First argument should be the directive 'v-else': we're only
    # interested in the actual ast node
    _, else_node = (
        if_else_statements.pop()
        if if_else_statements and if_else_statements[-1][0] == "v-else"
        else (None, None)
    )

    rewrite_name = RewriteName(skip=names)

    test = ast.parse(if_node.attrs[if_directive], mode="eval")
    root_statement = ast.IfExp(
        test=rewrite_name.visit(test).body,
        body=call_create_element(if_node, names=names),
        orelse=ast.Constant(value=None),
    )
    current_statement = root_statement

    for directive, node in if_else_statements:
        test = ast.parse(node.attrs[directive], mode="eval")
        if_else_tree = ast.IfExp(
            test=rewrite_name.visit(test).body,
            body=call_create_element(node, names=names),
            orelse=ast.Constant(value=None),
        )
        current_statement.orelse = if_else_tree
        current_statement = if_else_tree

    if else_node:
        current_statement.orelse = call_create_element(else_node, names=names)

    return root_statement


def is_directive(key):
    return key.startswith((DIRECTIVE_PREFIX, ":", "@"))


class NameCollector(ast.NodeVisitor):
    """AST node visitor that will create a set of the ids of every Name node
    it encounters."""

    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        self.names.add(node.id)


class LambdaNamesCollector(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_Lambda(self, node):
        # For some reason the body of a lambda is not visited
        # so we need to do it manually.
        visitor = LambdaNamesCollector()
        visitor.visit(node.body)
        self.names.update(visitor.names)

        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            self.names.add(arg.arg)


class RewriteName(ast.NodeTransformer):
    """AST node transformer that will try to replace static Name nodes with
    a call to `_lookup` with the name of the node."""

    def __init__(self, skip):
        self.skip = skip

    def visit_Name(self, node):
        # Don't try and replace any item from the __builtins__
        if node.id in __builtins__:
            return node

        # Don't replace any name that should be explicitely skipped
        if node.id in self.skip:
            return node

        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()),
                attr="_lookup",
                ctx=ast.Load(),
            ),
            args=[
                ast.Constant(value=node.id),
                ast.Call(
                    func=ast.Name(id="globals", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
            ],
            keywords=[],
        )


class ImportsCollector(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.names.add(alias.asname or alias.name)

    def visit_Import(self, node):
        for alias in node.names:
            self.names.add(alias.asname or alias.name)


class Node:
    """Node that represents an element from a CGX file."""

    def __init__(self, tag, attrs=None, location=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.location = location
        self.end = None
        self.data = None
        self.children = []

    def control_flow(self):
        """Returns the control flow string (if/else-if/else), if present in the
        attrs of the node."""
        for attr in self.attrs:
            if attr in CONTROL_FLOW_DIRECTIVES:
                return attr

    def child_with_tag(self, tag):
        for child in self.children:
            if child.tag == tag:
                return child


class CGXParser(HTMLParser):
    """Parser for CGX files.

    Creates a tree of Nodes with all encountered attributes and data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        # The tag parameter is lower-cased by the HTMLParser.
        # In order to figure out whether the tag indicates
        # an imported class, we need the original casing for
        # the tag.
        # Using the original start tag, we can figure out where
        # the tag is located using a lower-cased version. And then
        # use the index to extract the original casing for the tag.
        complete_tag = self.get_starttag_text()
        index = complete_tag.lower().index(tag)
        original_tag = complete_tag[index : index + len(tag)]
        node = Node(original_tag, dict(attrs), self.getpos())

        # Cast attributes that have no value to boolean (True)
        # so that they function like flags
        for key, value in node.attrs.items():
            if value is None:
                node.attrs[key] = True

        # Add item as child to the last on the stack
        self.stack[-1].children.append(node)
        # Make the new node the last on the stack
        self.stack.append(node)

    def handle_endtag(self, tag):
        # TODO: pop it till popping the same tag in order to
        # work around unclosed tags?
        # Pop the stack
        node = self.stack.pop()
        node.end = self.getpos()

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].data = data.strip()


def _print_ast_tree_as_code(tree):  # pragma: no cover
    """Handy function for debugging an ast tree"""
    try:
        import black
    except ImportError:
        return

    try:
        plain_result = ast.unparse(tree)
        result = black.format_file_contents(
            plain_result, fast=False, mode=black.mode.Mode()
        )
        print(result)  # noqa: T201
    except TypeError:
        pass

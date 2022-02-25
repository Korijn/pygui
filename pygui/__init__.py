from dataclasses import dataclass
import enum
from importlib.metadata import version
import time
from typing import Callable, Dict, List, Optional, Union

from observ import reactive, scheduler, watch
import pygfx as gfx
from PySide6 import QtCore

try:
    # If rich is available, use it to improve traceback logs
    from rich.traceback import install
    import shutil

    terminal_width = shutil.get_terminal_size((100, 20)).columns - 2
    install(width=terminal_width)
except ModuleNotFoundError:
    pass

from . import pygfx_renderer


__all__ = ["create_element", "PyGui"]
__version__ = version("pygui")


scheduler.register_qt()


class EffectTag(enum.Enum):
    UPDATE = "UPDATE"
    PLACEMENT = "PLACEMENT"
    DELETION = "DELETION"


@dataclass
class VNode:
    type: Union[str, Callable]
    props: Dict
    children: List["VNode"]
    key: Optional[str] = None


def create_element(type, props=None, *children) -> VNode:
    """Create an element description, based on type, props and (optionally) children"""
    key = props.pop("key") if props and "key" in props else None
    return VNode(type, props or {}, children or tuple(), key)


class PyGui:
    def __init__(self, *args, **kwargs):
        self.next_unit_of_work = None
        self.current_root = None
        self.wip_root = None
        self.deletions = None
        self.wip_fiber = None
        self.hook_index = None
        self.qt_timer = None
        self.render_callback = None

    def request_idle_work(self, deadline: int = None):
        """
        Schedules work to be done when all other Qt events have been handled.

        Args:
            deadline: targetted deadline for until when work can be done. If
                no deadline is given, then it will be set to 16ms from now.
        """
        if not self.qt_timer:
            self.qt_timer = QtCore.QTimer()
            self.qt_timer.setSingleShot(True)
            self.qt_timer.setInterval(0)
        else:
            self.qt_timer.timeout.disconnect()

        # current in ns
        if not deadline:
            deadline = time.perf_counter_ns() + 1000000 * 16

        self.qt_timer.timeout.connect(lambda: self.work_loop(deadline=deadline))
        self.qt_timer.start()

    def render(self, element, container, callback=None):
        self.wip_root = {
            "dom": container,
            "props": {},
            "children": [element],
            "alternate": self.current_root,
        }
        self.deletions = []
        self.next_unit_of_work = self.wip_root
        self.render_callback = callback

        self.request_idle_work()

    def work_loop(self, deadline: int):
        should_yield = False
        while self.next_unit_of_work and not should_yield:
            self.next_unit_of_work = self.perform_unit_of_work(self.next_unit_of_work)
            # yield if time is up
            now = time.perf_counter_ns()
            should_yield = (deadline - now) < 1 * 1000000

        if not self.next_unit_of_work and self.wip_root:
            self.commit_root()

        if self.next_unit_of_work:
            self.request_idle_work()
        else:
            if self.render_callback:
                self.render_callback()

    def create_dom(self, fiber) -> gfx.WorldObject:
        dom = pygfx_renderer.create_element(fiber["type"])
        update_dom(dom, {}, fiber["props"])
        return dom

    def update_function_component(self, fiber):
        self.wip_fiber = fiber
        self.hook_index = 0
        self.wip_fiber["hooks"] = []

        children = [fiber["type"](fiber["props"])]
        self.reconcile_children(fiber, children)

    def perform_unit_of_work(self, fiber):
        is_function_component = "type" in fiber and callable(fiber["type"])
        if is_function_component:
            self.update_function_component(fiber)
        else:
            self.update_host_component(fiber)

        # return next unit of work
        if child := fiber.get("child"):
            return child

        next_fiber = fiber
        while next_fiber:
            if sibling := next_fiber.get("sibling"):
                return sibling
            next_fiber = next_fiber.get("parent")

    def use_state(self, initial):
        initial = reactive(initial)

        old_hook = (
            self.wip_fiber.get("alternate")
            and self.wip_fiber["alternate"].get("hooks")
            and self.wip_fiber["alternate"]["hooks"][self.hook_index]
        )
        hook = {
            "state": old_hook["state"] if old_hook else initial,
            "queue": [],
        }

        actions = old_hook["queue"] if old_hook else []
        for action in actions:
            hook["state"] = action(hook["state"])

        def state_updated():
            # TODO: maybe check that the wip_root is None?
            # TODO: just queue the work instead?
            # assert wip_root is None
            self.wip_root = {
                "dom": self.current_root.get("dom"),
                "props": self.current_root.get("props"),
                "children": self.current_root["children"],
                "alternate": self.current_root,
            }
            self.next_unit_of_work = self.wip_root
            self.deletions = []
            self.request_idle_work()

        hook["watcher"] = watch(
            lambda: hook["state"],
            state_updated,
            deep=True,
        )

        self.wip_fiber["hooks"].append(hook)
        self.hook_index += 1
        return hook["state"]

    def update_host_component(self, fiber):
        # add dom node
        if not fiber["dom"]:
            fiber["dom"] = self.create_dom(fiber)

        # create new fibers
        self.reconcile_children(fiber, fiber["children"])

    def reconcile_children(self, wip_fiber, elements):
        index = 0
        old_fiber = wip_fiber.get("alternate") and wip_fiber.get("alternate").get(
            "child"
        )
        prev_sibling = None

        while index < len(elements) or old_fiber is not None:
            element = elements[index] if index < len(elements) else None
            new_fiber = None

            same_type = old_fiber and element and element.type == old_fiber["type"]

            if same_type:
                # update the node
                new_fiber = {
                    "type": old_fiber["type"],
                    "props": element.props,
                    "children": element.children,
                    "dom": old_fiber["dom"],
                    "parent": wip_fiber,
                    "alternate": old_fiber,
                    "effect_tag": EffectTag.UPDATE,
                }
            if element and not same_type:
                # add this node
                new_fiber = {
                    "type": element.type,
                    "props": element.props,
                    "children": element.children,
                    "dom": None,
                    "parent": wip_fiber,
                    "alternate": None,
                    "effect_tag": EffectTag.PLACEMENT,
                }
            if old_fiber and not same_type:
                # delete the old_fiber's node
                old_fiber["effect_tag"] = EffectTag.DELETION
                self.deletions.append(old_fiber)
            # TODO: we could use 'key's here for better reconciliation

            if old_fiber:
                old_fiber = old_fiber.get("sibling")

            if index == 0:
                wip_fiber["child"] = new_fiber
            elif element:
                prev_sibling["sibling"] = new_fiber

            prev_sibling = new_fiber
            index += 1

    def commit_root(self):
        for deletion in self.deletions:
            # TODO: should the deletions list be cleared at some point?
            self.commit_work(deletion)
        self.commit_work(self.wip_root.get("child"))
        self.current_root = self.wip_root
        self.wip_root = None

    def commit_deletion(self, fiber, dom_parent):
        if dom := fiber.get("dom"):
            dom_parent.remove(dom)
        else:
            self.commit_deletion(fiber["child"], dom_parent)

    def commit_work(self, fiber):
        if not fiber:
            return

        dom_parent_fiber = fiber.get("parent")
        while not dom_parent_fiber.get("dom"):
            dom_parent_fiber = dom_parent_fiber.get("parent")
        # pygfx object here (hence 'dom')
        dom_parent = dom_parent_fiber["dom"]

        if fiber.get("effect_tag") == EffectTag.PLACEMENT and fiber.get("dom"):
            # Add a 'renderer' and call the renderer with insert(element, parent)
            dom_parent.add(fiber["dom"])
        elif fiber.get("effect_tag") == EffectTag.UPDATE and fiber.get("dom"):
            update_dom(fiber["dom"], fiber["alternate"]["props"], fiber["props"])
        elif fiber.get("effect_tag") == EffectTag.DELETION:
            self.commit_deletion(fiber, dom_parent)

        self.commit_work(fiber.get("child"))
        self.commit_work(fiber.get("sibling"))


def update_dom(dom, prev_props, next_props):
    def is_event(key):
        return key.startswith("on")

    def is_property(key):
        return not is_event(key)

    def is_new(val, other, key):
        return val != other.get(key)

    # Remove old event listeners
    for name, val in prev_props.items():
        if not is_event(name):
            continue
        if name not in next_props or not is_new(val, next_props, name):
            continue

        event_type = name.lower()[2:]
        dom.remove_event_handler(event_type, val)

    # Remove old properties
    for key, val in prev_props.items():
        # is key an actual property?
        if not is_property(key):
            continue
        # is key gone?
        if key in next_props:
            continue

        # Supports resetting Vector3...
        pygfx_renderer.clear_attribute(dom, key, val)

    # Set new or changed properties
    for key, val in next_props.items():
        if not is_property(key):
            continue
        # is key new or changed?
        if not is_new(val, prev_props, key):
            continue

        # Only supports Vector3...
        pygfx_renderer.set_attribute(dom, key, val)

    # Add new event listeners
    for name, val in next_props.items():
        if not is_event(name):
            continue
        if not is_new(prev_props.get(name), next_props, name):
            continue

        event_type = name.lower()[2:]
        dom.add_event_handler(event_type, val)
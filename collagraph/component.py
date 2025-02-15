from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, ClassVar
from weakref import ref

from observ import reactive, readonly

if TYPE_CHECKING:
    from collagraph.fragment import ComponentFragment
    from collagraph.renderers import Renderer


class Component:
    """Abstract base class for components"""

    __lookup_cache__: ClassVar = defaultdict(dict)

    def __init__(self, props=None, parent=None):
        self._props = readonly({} if props is None else props)
        self._state = reactive({})
        self._element = None
        self._slots = {}
        self._event_handlers = defaultdict(set)
        self._lookup_cache = Component.__lookup_cache__[type(self)]
        self._parent = ref(parent) if parent else None
        self._provided = {}

    @property
    def props(self):
        """The incoming props of this component."""
        return self._props

    @props.setter
    def props(self, value):
        """Prevent overwriting the props attribute."""
        raise RuntimeError("Not allowed to override props attribute")

    @property
    def state(self):
        """The local state of this component."""
        return self._state

    @state.setter
    def state(self, value):
        """Prevent overwriting the state attribute."""
        raise RuntimeError("Not allowed to override state attribute")

    @property
    def element(self):
        """The root DOM element of this component."""
        return self._element

    @element.setter
    def element(self, value):
        """Prevent overwriting the element attributes."""
        raise RuntimeError("Not allowed to override element attribute")

    @property
    def parent(self):
        """
        The parent component of this component.
        For the root component, this returns None.
        """
        return self._parent and self._parent()

    @parent.setter
    def parent(self, value):
        """Prevent overwriting the parent attribute."""
        raise RuntimeError("Not allowed to override parent attribute")

    def mounted(self):
        """Called after the component has been mounted.

        A component is considered mounted after:

        * All of its child components have been mounted.
        * Its own DOM tree has been created and inserted into the parent container.
        """
        pass

    def updated(self):
        """Called after the component has updated its DOM tree.

        A parent component's updated method is called after that of its child
        components.
        """
        pass

    def before_unmount(self):
        """Called right before a component instance is to be unmounted.

        Use this method to clean up manually created side effects such as timers, DOM
        event listeners or server connections.

        Note that there are no specific guarantees about the order of when this method
        is called. A parent component's method might be called before that of its child
        components.
        """
        pass

    @abstractmethod
    def render(self, renderer: Renderer) -> ComponentFragment:  # pragma: no cover
        raise NotImplementedError

    def provide(self, key: str, value):
        self._provided[key] = value

    def inject(self, key, default=None):
        parent = self.parent
        while parent is not None:
            if key in parent._provided:
                return parent._provided[key]
            parent = parent.parent

        return default

    def emit(self, event, *args, **kwargs):
        """Call event handlers for the given event. Any args and kwargs will be passed
        on to the registered handlers."""
        for handler in self._event_handlers[event].copy():
            handler(*args, **kwargs)

    def add_event_handler(self, event, handler):
        """Adds an event handler for the given event."""
        self._event_handlers[event].add(handler)

    def remove_event_handler(self, event, handler):
        """Removes an event handler for the given event."""
        self._event_handlers[event].remove(handler)

    def _lookup(self, name, context):
        """
        Helper method that is used in the template.
        The method looks up variables that are mentioned in the template.
        This provides some syntactic sugar so that users can leave out `self`,
        `self.state` and `self.props`.
        """
        cache = self._lookup_cache
        if method := cache.get(name):
            return method(self, name, context)

        def props_lookup(self, name, context):
            return self.props[name]

        def state_lookup(self, name, context):
            return self.state[name]

        def self_lookup(self, name, context):
            return getattr(self, name)

        def global_lookup(self, name, context):
            return context[name]

        if name in self.props:
            cache[name] = props_lookup
        elif name in self.state:
            cache[name] = state_lookup
        elif hasattr(self, name):
            cache[name] = self_lookup
        elif name in context:
            cache[name] = global_lookup
        else:
            raise NameError(f"name '{name}' is not defined")
        return self._lookup(name, context)

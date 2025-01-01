"""Objects related to serializtion/deserialization context"""

import contextlib
import contextvars


class Context(contextlib.AbstractContextManager):
    _current_context: contextvars.ContextVar = contextvars.ContextVar("context")

    def __init__(self, context):
        self.context = context

    def __enter__(self):
        self.token = self._current_context.set(self.context)

    def __exit__(self, *args, **kwargs):
        self._current_context.reset(self.token)

    @classmethod
    def get(cls, default=...):
        if default is not ...:
            return cls._current_context.get(default)
        return cls._current_context.get()

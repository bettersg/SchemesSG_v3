"""Partner-facing request errors.

Its own module because both ``partner/api.py`` and ``partner/search.py`` raise it,
and ``search`` is imported lazily *by* ``api`` — importing the class from ``api``
would make that a cycle.
"""


class PartnerRequestError(Exception):
    """A client mistake whose message was written here and is safe to return.

    The handler used to catch bare ``ValueError`` and echo ``str(exc)`` into the
    400 body. That reads fine while every ValueError is one we raised, but the
    partner call path also runs Firestore, pandas and the shared catalog helpers —
    any ValueError from those would have had its internal message, and whatever
    field names or paths it mentions, handed to a partner verbatim. CodeQL flagged
    the same flow as stack-trace exposure.

    So: intentional client errors raise this, everything else is a logged 500.
    ``client_message`` is the literal we authored, kept as an explicit attribute
    so nothing has to stringify an exception to build a response.
    """

    def __init__(self, client_message: str):
        super().__init__(client_message)
        self.client_message = client_message

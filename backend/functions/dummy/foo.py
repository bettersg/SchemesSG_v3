"""
This is a dummy file for testing.

url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/foo
"""

from firebase_functions import https_fn, options


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Increases memory to 1GB
)
def foo(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello foo!")

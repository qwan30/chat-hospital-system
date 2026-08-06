import re

with open('app/backend/tests/cdi_v2/test_upload_sessions.py', 'r') as f:
    content = f.read()

# Fix imports
if 'StorageContentReader' not in content:
    content = content.replace(
        'from hospital_ai.services.upload_sessions import UploadSessionService',
        'from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader, MalwareScanResult'
    )

# Fix _CleanScanner
content = re.sub(
    r'async def scan\(self, key: str\) -> str:\n\s*return "clean"',
    'async def scan(self, key: str) -> MalwareScanResult:\n        return MalwareScanResult(status="clean")',
    content
)
content = re.sub(
    r'async def scan\(self, key: str\) -> str:\n\s*return "infected"',
    'async def scan(self, key: str) -> MalwareScanResult:\n            return MalwareScanResult(status="infected")',
    content
)

# Fix UploadSessionService
content = re.sub(
    r'UploadSessionService\(([^,]+),\s*([^,)]+)(,\s*scanner=([^)]+))?\)',
    r'UploadSessionService(\1, \2, content_reader=StorageContentReader(\2), scanner=\4)',
    content
)
content = content.replace('scanner=)', 'scanner=_CleanScanner())')

with open('app/backend/tests/cdi_v2/test_upload_sessions.py', 'w') as f:
    f.write(content)

with open('app/backend/tests/cdi_v2/test_upload_api.py', 'r') as f:
    content = f.read()

content = content.replace(
    '''        def mocked_from_request(sess, req):
            service = original_from_request(sess, req)
            service.storage = type(
                "MockStorage",
                (),
                {
                    "head_object": lambda *args: StorageObjectHead(args[-1], len(content), '"etag"', "application/pdf"),
                    "read_stream": lambda *args: io.BytesIO(content),
                },
            )()
            service.scanner = _CleanScanner()
            return service''',
    '''        def mocked_from_request(sess, req):
            service = original_from_request(sess, req)
            service.storage = type(
                "MockStorage",
                (),
                {
                    "head_object": lambda *args: StorageObjectHead(args[-1], len(content), '"etag"', "application/pdf"),
                    "read_stream": lambda *args: io.BytesIO(content),
                },
            )()
            from hospital_ai.services.upload_sessions import StorageContentReader
            service.content_reader = StorageContentReader(service.storage)
            service.scanner = _CleanScanner()
            return service'''
)

# Fix _CleanScanner in test_upload_api.py
content = re.sub(
    r'async def scan\(self, key: str\) -> str:\n\s*return "clean"',
    'async def scan(self, key: str):\n        from hospital_ai.services.upload_sessions import MalwareScanResult\n        return MalwareScanResult(status="clean")',
    content
)

with open('app/backend/tests/cdi_v2/test_upload_api.py', 'w') as f:
    f.write(content)

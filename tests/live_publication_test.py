"""Offline regression for Pages content and clinic-count verification."""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from verify_live_publication import FILES, verify


class Response:
    def __init__(self, data):
        self.content = data

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, data):
        self.data = data

    def get(self, url, **kwargs):
        return Response(self.data[url.rsplit("/regional-primary-care-availability/", 1)[-1]])


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    (root / "documents").mkdir()
    report = {"count": 1, "generated_on": "2026-11-13"}
    (root / "report.json").write_text(json.dumps(report))
    (root / "index.html").write_text(
        '<script id="clinic-data" type="application/json">'
        + json.dumps({"clinics": [{"id": "example"}], "generated_on": "2026-11-13"})
        + "</script>"
    )
    (root / FILES[2]).write_bytes(b"PK\\x03\\x04fake-zip")
    (root / FILES[3]).write_bytes(b"%PDF-1.7 fake")
    data = {name: (root / name).read_bytes() for name in FILES}
    url = "https://example.github.io/regional-primary-care-availability/"
    assert verify(url, root, session=FakeSession(data), attempts=1)["files"] == 4
    tampered = dict(data)
    tampered["report.json"] = b'{"count": 2}'
    try:
        verify(url, root, session=FakeSession(tampered), attempts=1)
        raise AssertionError("Mismatch must fail")
    except RuntimeError as exc:
        assert "report.json" in str(exc)
print("PASS: all four synchronized files accepted; mismatched report rejected")

import io

import pytest
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def post(name, data, ctype="application/octet-stream"):
    return client.post("/api/convert", files={"file": (name, io.BytesIO(data), ctype)})


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_html():
    r = post("a.html", b"<h1>Hello</h1><p>World <b>x</b></p>")
    assert r.status_code == 200
    assert "# Hello" in r.json()["markdown"]
    assert r.headers["cache-control"] == "no-store"


def test_csv():
    r = post("a.csv", b"a,b\n1,2\n")
    assert "| a | b |" in r.json()["markdown"]


def test_xlsx():
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["name", "qty"])
    wb.active.append(["apple", 3])
    b = io.BytesIO()
    wb.save(b)
    r = post("a.xlsx", b.getvalue())
    assert r.status_code == 200 and "apple" in r.json()["markdown"]


def test_empty():
    assert post("a.txt", b"").status_code == 422


def test_too_large(monkeypatch):
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 10)
    assert post("a.txt", b"x" * 100).status_code == 413


def test_corrupt_binary():
    r = post("a.pdf", bytes(range(256)) * 8)
    assert r.status_code in (415, 422)

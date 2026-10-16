# 확인: uv run pytest tests/test_stock.py  (진짜 인터넷은 부르지 않는다)
import requests

import stock


class FakeResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code}")


def naver_data(direction="RISING", status="OPEN"):
    return {
        "closePrice": "5,754.19",
        "compareToPreviousClosePrice": "199.97",
        "fluctuationsRatio": "3.60",
        "compareToPreviousPrice": {"code": "2", "text": "상승", "name": direction},
        "marketStatus": status,
    }


def test_get_index_reads_naver(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        assert url.endswith("/api/index/KOSPI/basic")
        return FakeResponse(naver_data())

    monkeypatch.setattr(requests, "get", fake_get)
    assert stock.get_index("KOSPI") == {
        "price": "5,754.19", "change": "199.97", "ratio": "3.60", "direction": "RISING", "open": True,
    }


def test_get_index_strips_sign(monkeypatch):
    data = naver_data("FALLING")
    data["compareToPreviousClosePrice"] = "-12.30"
    data["fluctuationsRatio"] = "-0.45"
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(data))
    index = stock.get_index("KOSDAQ")
    assert index["change"] == "12.30"
    assert index["ratio"] == "0.45"


def test_get_index_returns_none_when_offline(monkeypatch):
    def broken_get(*args, **kwargs):
        raise requests.ConnectionError("인터넷 끊김")

    monkeypatch.setattr(requests, "get", broken_get)
    assert stock.get_index("KOSPI") is None


def test_get_index_returns_none_when_shape_changes(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse({"something": "else"}))
    assert stock.get_index("KOSPI") is None


def test_index_text_rising_open(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(naver_data()))
    assert stock.index_text("KOSPI").startswith("코스피 5,754.19 ▲ 199.97 (3.60%) · 장중")


def test_index_text_falling_closed(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(naver_data("FALLING", "CLOSE")))
    text = stock.index_text("KOSDAQ")
    assert text.startswith("코스닥 5,754.19 ▼")
    assert "장 마감" in text
    assert "네이버 금융" in text


def test_index_text_when_fail(monkeypatch):
    monkeypatch.setattr(stock, "get_index", lambda code: None)
    assert stock.index_text("KOSPI") == "지금은 지수를 가져오지 못했어요."

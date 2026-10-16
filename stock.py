# 코스피·코스닥 지수를 네이버 금융에서 가져온다. 가입·키가 필요 없지만 공식 API가 아니다
# → 주소나 응답 모양이 예고 없이 바뀔 수 있다. 그래서 실패하면 None을 돌려주고 봇은 계속 돈다
import requests

URL = "https://m.stock.naver.com/api/index/{code}/basic"

NAMES = {"KOSPI": "코스피", "KOSDAQ": "코스닥"}

# 올랐는지 내렸는지는 숫자가 아니라 글자(name)로 온다 → 우리가 기호로 바꾼다
ARROWS = {"RISING": "▲", "UPPER_LIMIT": "▲", "FALLING": "▼", "LOWER_LIMIT": "▼"}


def get_index(code):
    """{'price': '5,754.19', 'change': '199.97', 'ratio': '3.60', 'direction': 'RISING', 'open': True}
    — 실패하면 None. code는 "KOSPI" 또는 "KOSDAQ"
    """
    try:
        # 브라우저인 척 User-Agent를 준다. timeout: 서버가 느려도 5초만 기다린다
        response = requests.get(
            URL.format(code=code), headers={"User-Agent": "Mozilla/5.0"}, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return {
            "price": data["closePrice"],
            # 방향은 direction으로 따로 알려 주므로 숫자의 부호는 떼어 둔다
            "change": data["compareToPreviousClosePrice"].lstrip("+-"),
            "ratio": data["fluctuationsRatio"].lstrip("+-"),
            "direction": data["compareToPreviousPrice"]["name"],
            "open": data["marketStatus"] == "OPEN",
        }
    except (requests.RequestException, KeyError, ValueError, AttributeError) as e:
        print(f"[지수 오류] {e}")
        return None


def index_text(code):
    index = get_index(code)
    if index is None:
        return "지금은 지수를 가져오지 못했어요."
    arrow = ARROWS.get(index["direction"], "-")  # 보합이거나 모르는 값이면 -
    status = "장중" if index["open"] else "장 마감"
    return (
        f"{NAMES[code]} {index['price']} {arrow} {index['change']} ({index['ratio']}%) · {status}\n"
        "(지수 데이터: 네이버 금융)"
    )

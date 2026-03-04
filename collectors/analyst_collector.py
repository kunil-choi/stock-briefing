# collectors/analyst_collector.py
import requests
from bs4 import BeautifulSoup

def collect_naver_research() -> list:
    """네이버 금융 리서치에서 최신 종목분석 리포트를 수집합니다."""
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    # 종목분석 리포트
    url = "https://finance.naver.com/research/company_list.naver"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("table.type_1 tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 5:
                stock_name = cols[0].get_text(strip=True)
                title = cols[1].get_text(strip=True)
                broker = cols[2].get_text(strip=True)
                date = cols[4].get_text(strip=True)
                link_tag = cols[1].select_one("a")
                link = ""
                if link_tag and link_tag.get("href"):
                    link = "https://finance.naver.com/research/" + link_tag["href"]

                if stock_name:
                    results.append({
                        "source_type": "애널리스트",
                        "source_name": f"{broker}",
                        "title": f"[{stock_name}] {title}",
                        "summary": f"종목: {stock_name}, 증권사: {broker}",
                        "link": link,
                        "published": date,
                    })
    except Exception as e:
        print(f"[애널리스트수집 오류] 네이버금융: {e}")

    return results


def collect_hankyung_consensus() -> list:
    """한경 컨센서스에서 최신 기업 리포트를 수집합니다."""
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    url = "https://markets.hankyung.com/consensus"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 리포트 목록 파싱 (한경 컨센서스 구조에 맞게 조정 필요)
        items = soup.select(".report-list li, .table_data tr, article")
        for item in items[:30]:
            title = item.get_text(strip=True)[:200]
            link_tag = item.select_one("a")
            link = ""
            if link_tag:
                href = link_tag.get("href", "")
                link = href if href.startswith("http") else "https://markets.hankyung.com" + href

            results.append({
                "source_type": "애널리스트",
                "source_name": "한경컨센서스",
                "title": title,
                "summary": "",
                "link": link,
                "published": "",
            })
    except Exception as e:
        print(f"[애널리스트수집 오류] 한경컨센서스: {e}")

    return results


def collect_analyst() -> list:
    """모든 애널리스트 소스를 통합 수집합니다."""
    results = []
    results.extend(collect_naver_research())
    results.extend(collect_hankyung_consensus())
    return results
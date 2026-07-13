import requests

from bs4 import BeautifulSoup


def download_html(url: str) -> BeautifulSoup:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise ValueError("Não foi possível baixar HTML do site.")

    return BeautifulSoup(response.text, "lxml")


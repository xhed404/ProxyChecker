from flask import Flask, render_template, request, jsonify
import requests
from requests.exceptions import RequestException, ConnectTimeout, ProxyError
import time


app = Flask(__name__)


TEST_URL = "https://httpbin.org/ip"
DEFAULT_TIMEOUT = 5


def check_proxy(proxy_url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    proxy_url = proxy_url.strip()
    if not proxy_url:
        return {
            "ok": False,
            "error": "Пустая строка прокси.",
        }

    if "://" not in proxy_url:
        proxy_url = f"http://{proxy_url}"

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    started = time.perf_counter()
    try:
        resp = requests.get(
            TEST_URL,
            proxies=proxies,
            timeout=timeout,
        )
        elapsed = (time.perf_counter() - started) * 1000
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "elapsed_ms": round(elapsed, 1),
            "ip": data.get("origin"),
        }
    except ConnectTimeout:
        return {
            "ok": False,
            "error": f"Таймаут при подключении (>{timeout} сек).",
        }
    except ProxyError as e:
        return {
            "ok": False,
            "error": f"Ошибка прокси: {e}",
        }
    except RequestException as e:
        return {
            "ok": False,
            "error": f"Ошибка запроса: {e}",
        }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/check", methods=["POST"])
def api_check():
    proxy = request.form.get("proxy", "").strip()
    timeout_raw = request.form.get("timeout", "").strip()

    try:
        timeout = int(timeout_raw) if timeout_raw else DEFAULT_TIMEOUT
        if timeout <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "error": "Некорректное значение таймаута."}), 400

    result = check_proxy(proxy, timeout=timeout)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(debug=True)


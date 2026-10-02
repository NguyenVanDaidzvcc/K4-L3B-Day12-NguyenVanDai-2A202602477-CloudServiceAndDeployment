"""Kiểm tra service thật; không in API key vào output."""

import argparse
import json
import os
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    local = httpx.URL(args.url).host in {"localhost", "127.0.0.1"}
    key = os.getenv("AGENT_API_KEY" if local else "DEPLOY_API_KEY")
    if not key:
        parser.error("Cần AGENT_API_KEY cho local hoặc DEPLOY_API_KEY cho cloud trong .env.")
    user = "smoke-" + uuid.uuid4().hex[:12]
    headers = {"X-API-Key": key, "X-User-Id": user}
    report = {"url": args.url, "user_id": user}
    with httpx.Client(base_url=args.url.rstrip("/"), timeout=60) as client:
        for endpoint in ("health", "ready"):
            response = client.get("/" + endpoint)
            report[endpoint] = {"status": response.status_code, "body": response.json()}
            assert response.status_code == 200, report[endpoint]
        response = client.post("/ask", json={"question": "Hello"})
        report["without_key"] = response.status_code
        assert response.status_code == 401
        responses = [
            client.post("/ask", headers=headers, json={"question": "Deploy là gì?"})
            for _ in range(15)
        ]
        report["request_statuses"] = [r.status_code for r in responses]
        report["history_lengths"] = [
            r.json()["history_length"] for r in responses if r.status_code == 200
        ]
        report["first_answer"] = responses[0].json()
        # Bài lab dùng cấu hình mặc định 10 request/phút.
        assert report["request_statuses"] == [200] * 10 + [429] * 5, report
        assert report["history_lengths"] == list(range(0, 20, 2)), report
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

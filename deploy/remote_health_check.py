from pathlib import Path
import urllib.error
import urllib.request


def read_token() -> str:
    env_path = Path("/app/rag-java-internal/.env")
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.startswith("RAG_SERVICE_TOKEN="):
            return raw.split("=", 1)[1].strip()
    return ""


def main() -> None:
    token = read_token()
    request = urllib.request.Request(
        "http://127.0.0.1:18020/internal/rag/health",
        headers={"X-RAG-Service-Token": token},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.status)
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(exc.code)
        print(exc.read().decode("utf-8"))


if __name__ == "__main__":
    main()

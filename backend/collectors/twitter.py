import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)
_BASE_URL = "https://api.twitterapi.io"


def fetch_new_tweets(api_key: str, username: str, since_id: str = "") -> list[dict]:
    """
    用 /twitter/user/last_tweets 拉取用户最新推文。
    since_id: 已知最新的 tweet id，只返回比它更新的推文。
    """
    headers = {"x-api-key": api_key}
    try:
        resp = httpx.get(
            f"{_BASE_URL}/twitter/user/last_tweets",
            headers=headers,
            params={"userName": username},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"拉取 @{username} 推文失败: {e}")
        return []

    tweets = data.get("data", {}).get("tweets") or []
    results = []
    for tw in tweets:
        parsed = _parse(tw, username)
        if not parsed:
            continue
        # 如果有 since_id，只保留更新的（ID 更大的）
        if since_id and parsed["tweet_id"] <= since_id:
            break
        results.append(parsed)

    return results


def _parse(tw: dict, fallback_author: str) -> dict | None:
    try:
        tweet_id = str(tw.get("id", ""))
        if not tweet_id:
            return None
        text = tw.get("text", "")
        if not text:
            return None
        author_obj = tw.get("author") or {}
        author = (
            author_obj.get("userName")
            or author_obj.get("screen_name")
            or fallback_author
        )
        created_raw = tw.get("createdAt") or ""
        return {
            "tweet_id": tweet_id,
            "source_id": f"twitter_{tweet_id}",
            "author": author,
            "content": text[:2000],
            "url": tw.get("url") or f"https://x.com/{author}/status/{tweet_id}",
            "tweeted_at": _parse_time(created_raw),
        }
    except Exception as e:
        logger.warning(f"解析推文失败: {e}")
        return None


def _parse_time(raw: str) -> datetime | None:
    if not raw:
        return None
    formats = [
        "%a %b %d %H:%M:%S +0000 %Y",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None

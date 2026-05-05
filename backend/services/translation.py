"""
MyMemory 免费翻译，无需 API Key，每日 1000 次（填邮箱可提升到 10000 次）
"""
import logging
import httpx

logger = logging.getLogger(__name__)


def translate(text: str, email: str = "") -> str:
    """翻译到中文，失败返回空字符串"""
    if not text or not text.strip():
        return ""
    # 截断，MyMemory 单次最多 500 字符
    chunk = text[:500]
    params = {"q": chunk, "langpair": "en|zh"}
    if email:
        params["de"] = email
    try:
        resp = httpx.get(
            "https://api.mymemory.translated.net/get",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("responseData", {}).get("translatedText", "")
        # MyMemory 在达到限额时返回 MYMEMORY WARNING
        if result and "MYMEMORY WARNING" in result:
            logger.warning("MyMemory 达到每日限额")
            return ""
        return result
    except Exception as e:
        logger.warning(f"翻译失败: {e}")
        return ""

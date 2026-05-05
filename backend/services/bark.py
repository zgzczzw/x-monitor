"""
Bark 推送通知服务
Bark 是一款 iOS 推送通知 App，支持自建服务器或官方服务器。
推送地址格式：https://{host}/{key}/{title}/{body}?url=...&sound=...
"""
import logging
import httpx

logger = logging.getLogger(__name__)


def send(
    server_url: str,
    device_key: str,
    title: str,
    body: str,
    url: str = "",
    sound: str = "",
    group: str = "X监控",
    icon: str = "",
) -> bool:
    """
    发送 Bark 推送通知。
    server_url: Bark 服务地址，如 https://api.day.app
    device_key: 设备 Key
    返回 True 表示发送成功。
    """
    if not server_url or not device_key:
        logger.warning("Bark 未配置，跳过推送")
        return False

    base = server_url.rstrip("/")
    endpoint = f"{base}/{device_key}"

    payload: dict = {
        "title": title[:64],
        "body": body[:256],
        "group": group,
    }
    if url:
        payload["url"] = url
    if sound:
        payload["sound"] = sound
    if icon:
        payload["icon"] = icon

    try:
        resp = httpx.post(endpoint, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200 or data.get("message") == "success":
            logger.info(f"Bark 推送成功: {title}")
            return True
        logger.warning(f"Bark 推送返回异常: {data}")
        return False
    except Exception as e:
        logger.error(f"Bark 推送失败: {e}")
        return False

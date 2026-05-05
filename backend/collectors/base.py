from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawPost:
    platform: str
    author: str
    content: str
    source_id: str        # 平台唯一 ID，用于去重
    url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


class BaseCollector:
    """所有采集器的基类，子类实现 collect 方法"""

    name: str = "base"

    def collect(self, keywords: list[str], limit: int = 20) -> list[RawPost]:
        """
        按关键词列表采集，返回 RawPost 列表。
        子类必须实现此方法，遇到异常应记录日志后返回空列表，不抛出。
        """
        raise NotImplementedError

    def is_configured(self) -> bool:
        """返回 True 表示凭据已配置，可以运行"""
        return True

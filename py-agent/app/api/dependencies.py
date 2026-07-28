#  ??? 这是干嘛的
from functools import lru_cache

from app.agent_langchain import Agent


#  这个用于缓存，所以创建的agent会被缓存
@lru_cache
def get_agent() -> Agent:
    """
    复用模型客户端和 LangChain Agent，
    不要每个请求都重新创建。
    """
    return Agent()
import os
import logging
import time
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


class HelloAgentsLLM:
    def __init__(
        self,
        model: str = None,
        apiKey: str = None,
        baseUrl: str = None,
        timeout: int = 120
    ):
        self.model = model or os.getenv("LLM_MODEL_ID", "llama-3.3-70b-versatile")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("错误：模型ID、API密钥或地址没填对，请检查 .env 文件。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)
        logger.info(f"LLM客户端初始化完成: {self.model}")

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> Optional[str]:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"请求模型: {self.model} (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                )

                collected_content = []
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    collected_content.append(content)
                result = "".join(collected_content)
                logger.info(f"模型回答完成，长度: {len(result)}")
                return result
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
        logger.error(f"API调用{MAX_RETRIES}次均失败")
        return None

    def invoke(self, messages: List[Dict[str, str]], temperature: float = 0) -> Optional[str]:
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=False,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
        return None

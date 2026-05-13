import os
import logging
import time
import json
from openai import OpenAI
from typing import List, Dict, Optional, Any
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

    def think_structured(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0
    ) -> Optional[Dict[str, Any]]:
        """Call LLM with function calling, return the parsed tool call arguments."""
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"结构化输出请求: {self.model} (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": tools[0]["function"]["name"]}},
                    stream=False,
                )

                choice = response.choices[0]
                if choice.message.tool_calls:
                    args_str = choice.message.tool_calls[0].function.arguments
                    logger.info(f"结构化输出完成，参数长度: {len(args_str)}")
                    return json.loads(args_str)

                # Fallback: model didn't call the tool, try to extract from content
                logger.warning("模型未调用工具，尝试从文本提取JSON")
                return None
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
            except Exception as e:
                logger.warning(f"结构化输出失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
        logger.error(f"结构化输出{MAX_RETRIES}次均失败")
        return None

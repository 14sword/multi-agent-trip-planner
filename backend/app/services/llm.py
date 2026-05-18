import os
import logging
import time
import json
import httpx
from openai import OpenAI
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY = 1


class HelloAgentsLLM:
    def __init__(
        self,
        model: str = None,
        apiKey: str = None,
        baseUrl: str = None,
        timeout: int = 180
    ):
        self.model = model or os.getenv("LLM_MODEL_ID", "llama-3.3-70b-versatile")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("错误：模型ID、API密钥或地址没填对，请检查 .env 文件。")

        # 绕过代理，直连 API
        http_client = httpx.Client(trust_env=False, timeout=timeout)
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout, http_client=http_client)
        logger.info(f"LLM客户端初始化完成: {self.model}")

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> Optional[str]:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"请求模型: {self.model} (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=False,
                )

                result = response.choices[0].message.content or ""
                logger.info(f"模型回答完成，长度: {len(result)}")
                return result
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
        logger.error(f"API调用{MAX_RETRIES}次均失败")
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

                # 模型未调用工具，尝试从文本内容提取 JSON
                content = choice.message.content or ""
                logger.warning(f"模型未调用工具，尝试从文本提取JSON (内容长度: {len(content)})")
                import re
                for pattern in [r'```json\s*(\{.*?\})\s*```', r'(\{[\s\S]*\})']:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        try:
                            parsed = json.loads(match.group(1))
                            if "city" in parsed and "days" in parsed:
                                logger.info("从文本中成功提取JSON")
                                return parsed
                        except json.JSONDecodeError:
                            continue
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

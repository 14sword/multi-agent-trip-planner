import os
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

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
        timeout = timeout

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("错误：模型ID、API密钥或地址没填对，请检查 .env 文件。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)
        print(f"🧠 LLM客户端初始化完成: {self.model}")

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        print(f"📡 请求模型: {self.model}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            collected_content = []
            print("✅ 模型开始回答：")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print("\n")
            return "".join(collected_content)
        except Exception as e:
            print(f"❌ 调用 API 出错啦: {e}")
            return None

    def invoke(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ 调用 API 出错啦: {e}")
            return None

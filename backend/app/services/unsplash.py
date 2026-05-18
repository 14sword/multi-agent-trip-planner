import logging
import httpx
from typing import Optional, List, Dict
from app.config import settings

logger = logging.getLogger(__name__)

class UnsplashService:
    def __init__(self):
        self.access_key = settings.UNSPLASH_ACCESS_KEY
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }
            response = httpx.get(url, params=params, timeout=10, trust_env=False)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            photos = []
            for result in results:
                photos.append({
                    "url": result["urls"]["regular"],
                    "description": result.get("description", ""),
                    "photographer": result["user"]["name"]
                })
            return photos
        except Exception as e:
            logger.warning(f"搜索图片失败: {e}")
            return []

    def get_photo_url(self, query: str) -> Optional[str]:
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None

#!/usr/bin/env python3
"""测试MCP连接"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.mcp_client import MCPClient

def test_mcp():
    print("🚀 开始测试MCP连接...")
    
    try:
        client = MCPClient()
        
        # 测试搜索POI
        print("\n📡 测试搜索POI: 北京天安门")
        result = client.search_poi("天安门", "北京")
        print(f"结果: {result}")
        
        # 测试获取天气
        print("\n🌤️ 测试获取天气: 北京")
        result = client.get_weather("北京")
        print(f"结果: {result}")
        
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp()
#!/usr/bin/env python
"""展示 AI Memos 功能的演示脚本。"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def print_json(data):
    """格式化打印 JSON 数据。"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """运行演示。"""
    print("=" * 60)
    print("AI Memos 演示")
    print("=" * 60)
    
    # 检查服务器健康状态
    print("\n1. 检查服务器健康状态...")
    response = requests.get(f"{BASE_URL}/health")
    print_json(response.json())
    
    # 创建备忘录
    print("\n2. 创建新备忘录...")
    memo1 = {
        "title": "FastAPI 最佳实践",
        "content": "始终使用类型提示、异步/等待 I/O 操作以及依赖注入。",
        "tags": ["fastapi", "python", "最佳实践"]
    }
    response = requests.post(f"{API_URL}/memos", json=memo1)
    memo1_data = response.json()
    memo1_id = memo1_data["id"]
    print_json(memo1_data)
    
    # 创建另一条备忘录
    print("\n3. 创建另一条备忘录...")
    memo2 = {
        "title": "PocketFlow 集成",
        "content": "PocketFlow 让构建 AI 驱动的工作流变得简单。",
        "tags": ["ai", "pocketflow", "工作流"]
    }
    response = requests.post(f"{API_URL}/memos", json=memo2)
    memo2_data = response.json()
    print_json(memo2_data)
    
    # 列出所有备忘录
    print("\n4. 列出所有备忘录...")
    response = requests.get(f"{API_URL}/memos")
    print_json(response.json())
    
    # 搜索备忘录
    print("\n5. 搜索 'fastapi'...")
    response = requests.get(f"{API_URL}/memos/search", params={"q": "fastapi"})
    print_json(response.json())
    
    # 更新备忘录
    print("\n6. 更新第一条备忘录...")
    update_data = {
        "title": "FastAPI 最佳实践（已更新）",
        "tags": ["fastapi", "python", "最佳实践", "已更新"]
    }
    response = requests.put(f"{API_URL}/memos/{memo1_id}", json=update_data)
    print_json(response.json())
    
    # 获取指定备忘录
    print("\n7. 获取更新后的备忘录...")
    response = requests.get(f"{API_URL}/memos/{memo1_id}")
    print_json(response.json())
    
    print("\n" + "=" * 60)
    print("演示成功完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到服务器。")
        print("请确保服务器正在运行：uv run aimemos")
    except Exception as e:
        print(f"错误：{e}")

"""测试脚本：验证聊天会话管理功能

此脚本测试聊天会话管理的基本功能，不依赖RAG。
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def print_response(response, title=""):
    """打印API响应"""
    print(f"\n{'='*60}")
    if title:
        print(f"{title}")
        print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"Response: {response.text[:500]}")


def test_chat_api():
    """测试聊天API"""
    
    print("聊天会话管理功能测试")
    print("="*60)
    
    # 1. 注册/登录用户
    print("\n1. 用户注册/登录")
    user_data = {
        "user_id": f"test_chat_user_{int(time.time())}",
        "password": "testpassword123"
    }
    
    # 尝试注册
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/register",
        json=user_data
    )
    
    if response.status_code == 409:  # 用户已存在
        print("用户已存在，直接登录")
    else:
        print_response(response, "注册用户")
    
    # 登录获取token
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json=user_data
    )
    print_response(response, "用户登录")
    
    if response.status_code != 200:
        print("登录失败，测试终止")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 创建聊天会话（不关联知识库）
    print("\n2. 创建聊天会话（不关联知识库）")
    session_data = {
        "title": "测试聊天会话"
    }
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/chats",
        json=session_data,
        headers=headers
    )
    print_response(response, "创建聊天会话")
    
    if response.status_code != 201:
        print("创建会话失败，测试终止")
        return
    
    session_id = response.json()["id"]
    print(f"会话ID: {session_id}")
    
    # 3. 获取会话列表
    print("\n3. 获取会话列表")
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/chats",
        headers=headers
    )
    print_response(response, "会话列表")
    
    # 4. 获取特定会话
    print("\n4. 获取特定会话")
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/chats/{session_id}",
        headers=headers
    )
    print_response(response, "会话详情")
    
    # 5. 更新会话标题
    print("\n5. 更新会话标题")
    update_data = {
        "title": "更新后的会话标题"
    }
    response = requests.put(
        f"{BASE_URL}{API_PREFIX}/chats/{session_id}",
        json=update_data,
        headers=headers
    )
    print_response(response, "更新会话")
    
    # 6. 获取会话消息（应该为空）
    print("\n6. 获取会话消息（初始应为空）")
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/chats/{session_id}/messages",
        headers=headers
    )
    print_response(response, "会话消息")
    
    # 7. 发送消息（流式响应）- 注意：这个会失败因为没有LLM，但可以验证端点存在
    print("\n7. 发送消息（流式响应）")
    print("注意：此测试会失败因为RAG功能未启用，但可验证端点工作正常")
    message_data = {
        "content": "你好！"
    }
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/chats/{session_id}/messages",
            json=message_data,
            headers=headers,
            stream=True,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        print("流式响应:")
        for line in response.iter_lines():
            if line:
                print(f"  {line.decode('utf-8')}")
    except requests.exceptions.Timeout:
        print("请求超时（预期行为，因为RAG未启用）")
    except Exception as e:
        print(f"错误: {e}")
    
    # 8. 删除会话
    print("\n8. 删除会话")
    response = requests.delete(
        f"{BASE_URL}{API_PREFIX}/chats/{session_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print("会话已删除" if response.status_code == 204 else "删除失败")
    
    # 9. 验证会话已删除
    print("\n9. 验证会话已删除")
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/chats/{session_id}",
        headers=headers
    )
    print_response(response, "获取已删除的会话（应返回404）")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("服务器运行正常，开始测试...")
            test_chat_api()
        else:
            print("服务器未正常运行")
    except requests.exceptions.RequestException as e:
        print(f"无法连接到服务器: {e}")
        print("请确保服务器已启动: uv run python -m aimemos.main")

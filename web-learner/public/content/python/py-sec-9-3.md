好的，总建筑师。作为您的 Python 技能金字塔专家和技术教育者，我将严格遵循您的教学设计图，将关于 `requests` 库的知识点转化为一篇高质量的 Markdown 教程。

---

### 🎯 核心目标 (Core Goal)

本节的核心目标是掌握使用 Python 中最流行的 HTTP 客户端库——`requests`，来与 Web API 进行交互。学完本节，你将能够自信地发送 HTTP 请求（如 GET 和 POST），处理服务器返回的响应，并从中提取所需的数据，这是构建任何需要与网络服务通信的应用程序的基石。

### 🔑 核心语法与参数 (Core Syntax & Parameters)

`requests` 库的设计理念是“为人类准备的 HTTP”，其语法极其简洁直观。最核心的功能由几个与 HTTP 方法同名的函数提供。

| 函数/方法             | 描述                                     | 常用参数                                                                                             |
| --------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `requests.get()`      | 发送一个 HTTP GET 请求，用于获取数据。     | `url` (必需), `params` (字典，用于 URL 查询参数), `headers` (字典，用于请求头), `timeout` (超时秒数)      |
| `requests.post()`     | 发送一个 HTTP POST 请求，用于提交数据。    | `url` (必需), `data` (字典/字符串，用于表单数据), `json` (字典，用于 JSON 数据), `headers`, `timeout`    |
| `response.status_code`| 响应对象的属性，返回一个整数表示 HTTP 状态码（例如 `200` 表示成功）。 | -                                                                                                    |
| `response.json()`     | 响应对象的方法，将 JSON 格式的响应体解码为 Python 字典或列表。 | -                                                                                                    |
| `response.text`       | 响应对象的属性，以字符串形式返回响应体内容。 | -                                                                                                    |
| `response.headers`    | 响应对象的属性，返回一个类字典对象，包含响应头信息。 | -                                                                                                    |

### 💻 基础用法 (Basic Usage)

让我们通过一个完整的 `code_example` 来看如何使用 `requests` 获取一个公开 API 的数据。我们将使用 JSONPlaceholder，一个为测试和原型设计而设的免费假 API。

**场景：获取一篇帖子的信息**

```python
import requests

# 1. 定义目标 API 的 URL
# 我们想要获取 id 为 1 的帖子
url = "https://jsonplaceholder.typicode.com/posts/1"

try:
    # 2. 发送 GET 请求
    # 这会返回一个 Response 对象
    response = requests.get(url)

    # 3. 检查响应状态码
    # 200 表示请求成功
    if response.status_code == 200:
        print("✅ 请求成功！")
        
        # 4. 处理 JSON 格式的响应数据
        # .json() 方法将 JSON 字符串自动转换为 Python 字典
        post_data = response.json()
        
        print("\n--- 帖子信息 ---")
        print(f"标题: {post_data['title']}")
        print(f"内容: {post_data['body']}")
        
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")

except requests.exceptions.RequestException as e:
    # 捕获可能出现的网络错误，如 DNS 查找失败、拒绝连接等
    print(f"请求过程中发生错误: {e}")
```

**输出：**

```
✅ 请求成功！

--- 帖子信息 ---
标题: sunt aut facere repellat provident occaecati excepturi optio reprehenderit
内容: quia et suscipit
suscipit recusandae consequuntur expedita et cum
reprehenderit molestiae ut ut quas totam
nostrum rerum est autem sunt rem eveniet architecto
```

这个简单的例子覆盖了从发送请求、检查状态到解析 JSON 数据的完整流程，是使用 `requests` 库最核心、最常见的操作。

### 🧠 深度解析 (In-depth Analysis)

为了更灵活地与 API 交互，我们需要理解如何定制我们的请求。

#### 1. HTTP 请求方法：GET vs. POST

-   **GET**: 用于**请求**数据。它应该是幂等的（多次请求结果相同），并且所有参数都附加在 URL 的查询字符串中。就像在浏览器地址栏输入网址访问页面。
-   **POST**: 用于**提交**数据以在服务器上创建或更新资源。数据包含在请求体中，而不是 URL 中。就像填写网页表单并点击“提交”按钮。

#### 2. 传递查询参数 (`params`)

当使用 GET 请求时，我们常常需要传递参数来筛选或指定数据，例如 `?page=2&limit=10`。`requests` 允许我们用一个字典来构造它，这比手动拼接字符串更安全、更清晰。

```python
# 获取用户 ID 为 1 的所有帖子
base_url = "https://jsonplaceholder.typicode.com/posts"
query_params = {
    "userId": 1,
    "_limit": 2  # 自定义参数，限制返回数量为2
}

response = requests.get(base_url, params=query_params)

# requests 会自动将 URL 构造成: 
# https://jsonplaceholder.typicode.com/posts?userId=1&_limit=2
print(f"请求的 URL: {response.url}")

# 打印获取到的帖子标题
if response.status_code == 200:
    posts = response.json()
    for post in posts:
        print(f"- {post['title']}")
```

#### 3. 传递请求头 (`headers`)

HTTP 请求头用于传递关于请求的元数据，例如客户端类型（`User-Agent`）、可接受的内容类型（`Accept`）或认证令牌（`Authorization`）。许多 API 要求设置特定的请求头。

```python
url = "https://api.github.com/users/python"
# 很多 API 要求提供 User-Agent
custom_headers = {
    "User-Agent": "MyAwesomePythonApp/1.0",
    "Accept": "application/vnd.github.v3+json" # 指定接受的 API 版本
}

response = requests.get(url, headers=custom_headers)

if response.status_code == 200:
    user_data = response.json()
    print(f"GitHub 用户 'python' 的公开仓库数量: {user_data['public_repos']}")
else:
    print(f"请求失败: {response.status_code}")
```

通过 `params` 和 `headers`，我们可以精细地控制发送的请求，满足绝大多数 API 的交互要求。

### ⚠️ 常见陷阱与最佳实践 (Common Pitfalls & Best Practices)

1.  **陷阱：从不检查状态码**
    *   **问题**：直接调用 `response.json()` 而不检查 `response.status_code`。如果请求失败（如 404 Not Found 或 500 Server Error），服务器返回的可能不是 JSON，此时调用 `.json()` 会抛出 `JSONDecodeError` 异常。
    *   **最佳实践**：总是先检查状态码。更简洁的方式是使用 `response.raise_for_status()`，它会在状态码为 4xx 或 5xx 时自动抛出 `HTTPError` 异常，非常适合结合 `try...except` 使用。

    ```python
    try:
        response = requests.get("https://httpbin.org/status/404")
        response.raise_for_status()  # 如果状态码是 4xx 或 5xx，这里会抛出异常
        data = response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP 错误发生: {err}") # 输出: HTTP 错误发生: 404 Client Error: NOT FOUND for url: ...
    ```

2.  **陷阱：网络请求无限期等待**
    *   **问题**：如果服务器响应缓慢或网络连接有问题，`requests` 调用可能会永远挂起，阻塞你的程序。
    *   **最佳实践**：始终设置 `timeout` 参数。这是一个很好的防御性编程习惯。`timeout` 可以是一个数字（连接和读取的总超时），也可以是一个元组 `(connect_timeout, read_timeout)`。

    ```python
    try:
        # 设置总超时为 5 秒
        response = requests.get("https://httpbin.org/delay/10", timeout=5)
    except requests.exceptions.Timeout:
        print("请求超时！服务器在5秒内没有响应。")
    ```

3.  **最佳实践：对同一主机的多次请求使用会话（Session）**
    *   **原因**：如果你需要对同一个网站发送多次请求，使用 `requests.Session` 对象可以显著提升性能。`Session` 会保持 TCP 连接，并自动处理 Cookies，就像浏览器一样。
    *   **用法**：

    ```python
    with requests.Session() as session:
        # 这个 session 会复用底层的 TCP 连接
        response1 = session.get("https://httpbin.org/get")
        response2 = session.get("https://httpbin.org/get")
        print("使用 Session 完成两次请求。")
    ```

### 🚀 实战演练 (Practical Exercise)

**案例研究 (Case Study): 构建一个简单的天气查询工具**

让我们综合运用所学知识，编写一个脚本，通过调用免费的 [Open-Meteo 天气 API](https://open-meteo.com/) 来查询指定城市的当前天气。

**任务：**
1.  获取指定经纬度的当前天气信息。
2.  从返回的 JSON 数据中，提取并显示当前温度和风速。

```python
import requests

def get_current_weather(latitude, longitude):
    """
    查询并打印指定经纬度的当前天气。
    """
    API_URL = "https://api.open-meteo.com/v1/forecast"
    
    # 1. 准备查询参数
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true"  # 告诉 API 我们需要当前天气数据
    }
    
    # 2. 准备请求头，表明我们的应用身份
    headers = {
        "User-Agent": "MyWeatherApp/1.0 (https://myweatherapp.com)"
    }
    
    print(f"正在查询经纬度 ({latitude}, {longitude}) 的天气...")

    try:
        # 3. 发送 GET 请求，并设置超时
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        
        # 4. 检查请求是否成功
        response.raise_for_status()
        
        # 5. 解析 JSON 数据
        weather_data = response.json()
        current_weather = weather_data.get("current_weather")
        
        if current_weather:
            temperature = current_weather.get("temperature")
            windspeed = current_weather.get("windspeed")
            
            # 6. 格式化并打印结果
            print("\n--- 实时天气 ---")
            print(f"🌡️  温度: {temperature}°C")
            print(f"💨  风速: {windspeed} km/h")
        else:
            print("未能从 API 响应中找到当前天气数据。")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误: {req_err}")

# --- 主程序执行 ---
if __name__ == "__main__":
    # 以北京的经纬度为例
    beijing_lat = 39.9042
    beijing_lon = 116.4074
    get_current_weather(beijing_lat, beijing_lon)
```
这个实战演练让你将 `params`、`headers`、`timeout` 和错误处理等知识点整合在了一个有实际意义的 `case_study` 中。

### 💡 总结 (Summary)

`requests` 库是 Python 生态中进行网络编程的瑞士军刀。通过本节的学习，我们解锁了与 Web API 通信的核心能力。

**关键回顾：**
-   **核心函数**：`requests.get()` 用于获取数据，`requests.post()` 用于提交数据。
-   **响应对象**：`response` 对象是交互的中心，通过 `.status_code` 检查成功与否，通过 `.json()` 或 `.text` 获取数据。
-   **请求定制**：使用 `params` 字典传递 URL 查询参数，使用 `headers` 字典发送自定义请求头。
-   **健壮性**：始终通过 `response.raise_for_status()` 或检查 `.status_code` 来处理潜在的请求失败，并使用 `timeout` 参数防止程序无限期阻塞。

掌握了 `requests`，你就打开了通往海量网络数据和服务的大门，为后续学习爬虫、构建微服务客户端或与任何第三方服务集成打下了坚实的基础。
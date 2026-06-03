# 导入 requests，用来向高德地图接口发送 HTTP 请求。
import requests

# 导入高德地图 API Key。
from config import AMAP_KEY


# 设置网络请求超时时间，避免接口卡住太久。
REQUEST_TIMEOUT = 8
# 设置兜底城市；如果 IP 定位失败，可以人工改成你所在城市。
DEFAULT_CITY = "南昌"


# 定义通过公网 IP 定位当前城市的函数。
def get_location_by_ip() -> dict:
    # 高德 IP 定位接口地址。
    url = "https://restapi.amap.com/v3/ip"
    # 发送 GET 请求，把 key 作为参数传给高德。
    resp = requests.get(url, params={"key": AMAP_KEY}, timeout=REQUEST_TIMEOUT)
    # 如果 HTTP 状态码不是 2xx，就抛出异常。
    resp.raise_for_status()
    # 把接口返回的 JSON 字符串解析成 Python 字典。
    data = resp.json()

    # 高德返回 status=1 表示成功。
    if data.get("status") != "1":
        # 如果失败，抛出异常并带上原始返回，方便排查。
        raise Exception(f"IP 定位接口返回异常: {data}")

    # 读取城市名，例如“南昌市”。
    city = data.get("city")
    # 读取行政区编码，例如“360100”；天气接口用 adcode 更稳定。
    adcode = data.get("adcode")
    # 读取省份名，例如“江西省”。
    province = data.get("province")

    # 某些 IP 无法定位到城市时，高德可能返回空列表。
    if isinstance(city, list) or not city:
        # 如果城市不可用，就用省份兜底。
        city = province
    # 如果 adcode 不可用，就临时用 city 兜底。
    if isinstance(adcode, list) or not adcode:
        # 这里用城市名也可以查询天气。
        adcode = city

    # 如果城市和 adcode 都没有，就说明定位失败。
    if not city and not adcode:
        # 抛出异常，告诉调用方没有有效定位信息。
        raise Exception(f"IP 定位未返回有效城市: {data}")

    # 返回整理后的定位信息。
    return {
        # 当前 IP 所在城市。
        "city": city,
        # 当前 IP 所在行政区编码。
        "adcode": adcode,
        # 当前 IP 所在省份。
        "province": province,
        # 高德返回的矩形范围，可用于调试定位精度。
        "rectangle": data.get("rectangle"),
    }


# 定义获取天气的函数；city 不传时自动按 IP 定位。
def get_weather(city: str | None = None) -> dict:
    # location 用来保存 IP 定位结果；手动传 city 时它保持 None。
    location = None
    # query_city 是最终传给天气接口的城市名或 adcode。
    query_city = city

    # 如果调用者没有指定城市，就进行 IP 定位。
    if not query_city:
        # 调用 IP 定位接口获取当前位置。
        location = get_location_by_ip()
        # 优先用 adcode 查天气；没有 adcode 再用城市名；再不行用默认城市。
        query_city = location["adcode"] or location["city"] or DEFAULT_CITY

    # 高德实时天气接口地址。
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    # 组装天气接口参数。
    params = {
        # 高德 API Key。
        "key": AMAP_KEY,
        # 查询城市，可以是中文城市名，也可以是 adcode。
        "city": query_city,
        # base 表示实时天气；all 表示预报天气。
        "extensions": "base",
    }
    # 发送天气请求。
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    # 如果 HTTP 请求失败，就抛出异常。
    resp.raise_for_status()
    # 把天气接口返回解析成字典。
    data = resp.json()

    # status=1 且 count>=1 表示至少有一条天气数据。
    if data.get("status") == "1" and int(data.get("count", 0)) >= 1:
        # lives[0] 是当前城市的实时天气。
        live = data["lives"][0]
        # 返回项目需要的天气字段。
        return {
            # 城市名。
            "city": live["city"],
            # 天气现象，例如“多云”。
            "weather": live["weather"],
            # 温度，单位摄氏度。
            "temperature": live["temperature"],
            # 风向。
            "winddirection": live["winddirection"],
            # 湿度百分比。
            "humidity": live["humidity"],
            # 高德天气更新时间。
            "reporttime": live["reporttime"],
            # 标记天气来源：ip 表示自动定位，manual 表示手动城市。
            "location_source": "ip" if location else "manual",
            # 省份信息；自动定位时来自 IP 定位，手动城市时来自天气接口。
            "province": location.get("province") if location else live.get("province"),
        }

    # 如果接口返回格式不符合预期，就抛出异常。
    raise Exception(f"天气接口返回异常: {data}")


# 只有直接运行 python fetchers/weather.py 时才执行下面测试代码。
if __name__ == "__main__":
    # 用 try 捕获测试过程中的异常。
    try:
        # 打印当前 IP 定位到的天气。
        print(get_weather())
    # 捕获异常并打印错误信息。
    except Exception as e:
        # 输出错误原因。
        print(f"出错: {e}")

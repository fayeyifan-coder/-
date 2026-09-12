import os
import requests

# 环境变量读取
QWEATHER_KEY = os.getenv("QWEATHER_KEY")
BARK_KEY = os.getenv("BARK_KEY")
CITY_NAME = os.getenv("CITY_NAME", "北京")


def get_location_id(city_name):
    """查询城市 Location ID"""
    url = f"https://geoapi.qweather.com/v2/city/lookup?location={city_name}&key={QWEATHER_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("code") == "200" and res.get("location"):
            return res["location"][0]["id"], res["location"][0]["name"]
    except Exception as e:
        print(f"[错误] 查询城市 ID 失败: {e}")
    return None, city_name


def get_weather_data(location_id):
    """获取今日天气与穿衣/出行生活指数"""
    # 3天天气预报接口
    weather_url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={QWEATHER_KEY}"
    # 生活指数接口 (3: 穿衣, 6: 旅游/出行)
    indices_url = f"https://devapi.qweather.com/v7/indices/1d?location={location_id}&key={QWEATHER_KEY}&type=3,6"

    try:
        w_res = requests.get(weather_url, timeout=10).json()
        i_res = requests.get(indices_url, timeout=10).json()

        if w_res.get("code") != "200":
            return None

        today = w_res["daily"][0]

        dressing_idx = "暂无建议"
        travel_idx = "暂无建议"

        if i_res.get("code") == "200":
            for item in i_res.get("daily", []):
                if item["type"] == "3":
                    dressing_idx = f"{item['category']}（{item['text']}）"
                elif item["type"] == "6":
                    travel_idx = f"{item['category']}（{item['text']}）"

        return {
            "textDay": today["textDay"],
            "textNight": today["textNight"],
            "tempMin": today["tempMin"],
            "tempMax": today["tempMax"],
            "windDir": today["windDirDay"],
            "windScale": today["windScaleDay"],
            "dressing": dressing_idx,
            "travel": travel_idx,
        }
    except Exception as e:
        print(f"[错误] 请求天气数据失败: {e}")
        return None


def send_bark(title, content):
    """推送至 Bark"""
    url = f"https://api.day.app/{BARK_KEY}"
    payload = {
        "title": title,
        "body": content,
        "group": "天气早报",
        "icon": "https://cdn-icons-png.flaticon.com/512/1163/1163661.png",
    }
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        if res.get("code") == 200:
            print("[成功] 天气通知已成功推送给 Bark！")
        else:
            print(f"[失败] Bark 响应异常: {res}")
    except Exception as e:
        print(f"[错误] Bark 请求失败: {e}")


def main():
    if not QWEATHER_KEY or not BARK_KEY:
        print("[错误] 缺失必要环境变量：QWEATHER_KEY 或 BARK_KEY")
        return

    location_id, real_city_name = get_location_id(CITY_NAME)
    if not location_id:
        print(f"[错误] 无法获取城市 [{CITY_NAME}] 的 ID")
        return

    data = get_weather_data(location_id)
    if not data:
        print("[错误] 无法读取天气数据")
        return

    title = f"☀️ {real_city_name} 今日天气提醒"
    content = (
        f"天气：{data['textDay']}（夜间 {data['textNight']}）\n"
        f"气温：{data['tempMin']}℃ ~ {data['tempMax']}℃\n"
        f"风力：{data['windDir']} {data['windScale']}级\n"
        f"----------------------\n"
        f"👔 穿衣：{data['dressing']}\n"
        f"🚗 出行：{data['travel']}"
    )

    send_bark(title, content)


if __name__ == "__main__":
    main()

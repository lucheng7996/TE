import os
import requests
import re
import base64
import cv2
import datetime
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 获取rtp目录下的文件名
files = os.listdir('files')

files_name = []

# 去除后缀名并保存至provinces_isps
for file in files:
    name, extension = os.path.splitext(file)
    files_name.append(name)

# 忽略不符合要求的文件名
provinces_isps = [name for name in files_name if name.count('_') == 1]

# 打印结果
print(f"本次查询：{provinces_isps}的组播节目")

for province_isp in provinces_isps:
    province, isp = province_isp.split("_")
    # 根据不同的 isp 设置不同的 org 值
    org = "Chinanet"

    if isp == "电信":
        asn = "4134"  # org = "Chinanet"
    elif isp == "联通":
        asn = "4837"  # org = "CHINA UNICOM China169 Backbone"
    else:
        org = ""

    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()
    str_channels = ''
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{org}\"'
            # 将字符串编码为字节流
            bytes_string = search_txt.encode('utf-8')
            # 使用 base64 进行编码
            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} 查询运营商 : {province}{isp} ，查询网址 : {search_url}")
            response = requests.get(search_url, timeout=30)
            # 处理响应
            response.raise_for_status()
            # 检查请求是否成功
            html_content = response.text
            # 使用BeautifulSoup解析网页内容
            html_soup = BeautifulSoup(html_content, "html.parser")
            # print(f"{current_time} html_content:{html_content}")
            # 查找所有符合指定格式的网址
            # 设置匹配的格式，如http://8.8.8.8:8888
            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, html_content)
            # 去重得到唯一的URL列表
            result_urls = set(urls_all)
            print(f"{current_time} result_urls:{result_urls}")
            # 在rtp文件夹添加[省份-运营商.txt]组播文件，然后在下面同格式添加一个对应的任一组播ip
            # 对应省份的组播地址:重庆联通cctv1：225.0.4.74:7980，重庆电信cctv1:235.254.199.51:7980，广东电信广东卫视239.77.1.19:5146
            pro_isp = province + isp
            # urls_udp = "/udp/239.77.1.19:5146"
            if pro_isp == "北京联通":
                urls_udp = "/udp/239.3.1.129:8008"
            elif pro_isp == "湖南电信":
                urls_udp = "/udp/239.76.246.151:1234"
            elif pro_isp == "福建电信":
                urls_udp = "/udp/239.61.3.61:9884"
            elif pro_isp == "四川电信":
                urls_udp = "/udp/239.93.0.184:5140"
            elif pro_isp == "广东电信":
                urls_udp = "/udp/239.77.1.17:5146"
            else:
                org = ""

            valid_ips = []

            # 遍历所有视频链接
            for url in result_urls:
                ip_port = url.replace("http://", "")
                video_url = url + urls_udp

                # 用OpenCV读取视频
                cap = cv2.VideoCapture(video_url)

                # 检查视频是否成功打开
                if not cap.isOpened():
                    print(f"{current_time} {video_url} 无效")
                else:
                    # 读取视频的宽度和高度
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    print(f"{current_time} {video_url} 的分辨率为 {width}x{height}")
                    # 检查分辨率是否大于0
                    if width > 0 and height > 0:
                        valid_ips.append(ip_port)
                    # 关闭视频流
                    cap.release()

            if valid_ips:
                # 生成节目列表
                rtp_filename = f'files/{province}_{isp}.txt'
                with open(rtp_filename, 'r', encoding='utf-8') as file:
                    data = file.read()
                txt_filename = f'{province}{isp}.txt'
                with open(txt_filename, 'w') as new_file:
                    for ip in valid_ips:
                        new_data = data.replace("rtp://", f"http://{ip}/udp/")
                        new_file.write(new_data)

                print(f'已生成播放列表，保存至{txt_filename}')

                # print(f'已保存至{m3u_filename}')

            else:
                print("未找到合适的 IP 地址。")

        except (requests.Timeout, requests.RequestException) as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生超时，异常次数：{timeout_cnt}")
            if timeout_cnt <= 5:
                # 继续下一次循环迭代
                continue
            else:
                print(f"{current_time} 搜索IPTV频道源[]，超时次数过多：{timeout_cnt} 次，停止处理")

import os
import requests
import re
import base64
import cv2
#import datetime
from datetime import datetime
from bs4 import BeautifulSoup
#from urllib.parse import urlparse
# pip3 install translate
from translate import Translator

# 获取udp目录下的文件名
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

keywords = []

for province_isp in provinces_isps:
    # 读取文件并删除空白行
    try:
        with open(f'files/{province_isp}.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines if line.strip()]
        # 获取第一行中以包含 "udp://" 的值作为 mcast
        if lines:
            first_line = lines[1]
            if "udp://" in first_line:
                mcast = first_line.split("udp://")[1].split(" ")[0]
                keywords.append(province_isp + "_" + mcast)
    except FileNotFoundError:
        # 如果文件不存在，则捕获 FileNotFoundError 异常并打印提示信息
        print(f"文件 '{province_isp}.txt' 不存在. 跳过此文件.")

for keyword in keywords:
    province, isp, mcast = keyword.split("_")
    # 将省份转成英文小写
    translator = Translator(from_lang='chinese', to_lang='english')
    province_en = translator.translate(province)
    province_en = province_en.lower()
    # 根据不同的 isp 设置不同的 org 值
    org = "Chinanet"
    if isp == "电信":
        org = "Chinanet"
        isp_en = "ctcc"
        asn = "4134"
    elif isp == "联通":
        isp_en = "cucc"
        org = "CHINA UNICOM China169 Backbone"
        asn = "4837"
    elif isp == "联通" and province_en =="beijing":
        asn = "4808"
    else:
        asn = ""
        org = ""

    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && asn=\"{asn}\"'
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

            valid_ips = []

            # 遍历所有视频链接
            for url in result_urls:
                video_url = url + "/udp/" + mcast

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
                        valid_ips.append(url)
                    # 关闭视频流
                    cap.release()

            if valid_ips:
                # 生成节目列表 省份运营商.txt
                out_path = 'outfiles'
                if not os.path.exists(out_path):
                    #文件夹不存在，需要创建
                    print(f"文件夹 '{out_path}' 不存在，创建。")
                    os.makedirs(out_path)
                #out_path = os.path.abspath('outfiles')
                udp_filename = f'files/{province}_{isp}.txt'
                with open(udp_filename, 'r', encoding='utf-8') as file:
                    data = file.read()
                txt_filename = f'files/{province_en}{isp_en}.txt'
                with open(txt_filename, 'w') as new_file:
                    for url in valid_ips:
                        new_data = data.replace("udp://", f"{url}/udp/")
                        new_file.write(new_data)

                print(f'已生成播放列表，保存至{txt_filename}')

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

# 获取outfiles目录下的文件名
files1 = os.listdir('outfiles')
file_contents = []
for file_path in files1:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)

# 写入合并后的txt文件
with open("IPTV_UDP.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))
    # 写入更新日期时间
    # file.write(f"{now_today}更新,#genre#\n")
    # 获取当前时间
    local_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(local_tz)
    #now = datetime.now()
    output.write(f"\n更新时间,#genre#\n")
    output.write(f"{now.strftime("%Y-%m-%d")},url\n")
    output.write(f"{now.strftime("%H:%M:%S")},url\n")

output.close()

print(f"电视频道成功写入IPTV_UDP.txt")

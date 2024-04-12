import time
import os
import re
import base64
import requests
import threading
from queue import Queue
from datetime import datetime

#  获取远程直播源文件
url = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Fairy8o/IPTV/main/DIYP-v4.txt"
r = requests.get(url)
open('DIYP-v4.txt', 'wb').write(r.content)

keywords = ['凤凰卫视', '凤凰资讯', 'TVB翡翠', 'TVB明珠', 'TVB星河', 'J2', '无线', '有线', '天映', 'VIU', 'RTHK', 'HOY',
            '香港卫视', 'Viut']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
with open('DIYP-v4.txt', 'r', encoding='utf-8') as file, open('HK.txt', 'w', encoding='utf-8') as HK:
    HK.write('\n港澳频道,#genre#\n')
    for line in file:
        if re.search(pattern, line):  # 如果行中有任意关键字
            HK.write(line)  # 将该行写入输出文件

keywords = ['民视', '中视', '台视', '华视', '新闻台', '东森', '龙祥', '公视', '三立', '大爱', '年代新闻', '人间卫视',
            '人間', '大立']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
with open('DIYP-v4.txt', 'r', encoding='utf-8') as file, open('TW.txt', 'w', encoding='utf-8') as TW:
    TW.write('\n台湾频道,#genre#\n')
    for line in file:
        if re.search(pattern, line):  # 如果行中有任意关键字
            TW.write(line)  # 将该行写入输出文件

# 读取要合并的香港频道和台湾频道文件
file_contents = []
file_paths = ["HK.txt", "TW.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)
# 生成合并后的文件
with open("GAT.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))

# 线程安全的队列，用于存储下载任务
task_queue = Queue()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 '
                  'Safari/537.36'}


# 文件读取
class Record:
    def __init__(self, name, url):
        self.name = name  # 频道名称
        self.url = url  # 频道链接

    def __str__(self):
        return f"{self.name},{self.url}"


# 抽象类读取文件
class FileReader:

    def read_data(self) -> list[Record]:
        '''读取文件的数据'''
        pass


class TextFileReader(FileReader):

    def __init__(self, path):
        self.path = path  # 定义成员变量记录文件路径

    def read_data(self) -> list[Record]:
        f = open(self.path, "r", encoding="UTF-8")
        record_list = []
        for line in f.readlines():
            data_list = line.strip().split(",")
            record = Record(data_list[0], data_list[1])
            record_list.append(record)

        f.close()
        return record_list


class GetChannel():

    def __init__(self, urls, org = "Chinanet"):
        self.urls = urls
        self.org = org

    def get_channel(self):
        urls_a = []
        urls_all = []
        count = 0
        for url in self.urls:
            url_0 = str(base64.b64encode((f'"Server: udpxy" && city="{url}" && org="{self.org}"').encode("utf-8")),
                        "utf-8")
            url_64 = f'https://fofa.info/result?qbase64={url_0}'
            print(url_64)
            try:
                response = requests.get(url_64, headers=headers, timeout=15)
                page_content = response.text
                pattern = r'href="(http://\d+\.\d+\.\d+\.\d+:\d+)"'
                page_urls = re.findall(pattern, page_content)
                for urlx in page_urls:
                    try:
                        response = requests.get(url=urlx + '/status', timeout=1)
                        response.raise_for_status()  # 返回状态码不是200异常
                        page_content = response.text
                        #pattern = r'class="proctabl"'
                        pattern = r'value="Restart"'
                        page_proctabl = re.findall(pattern, page_content)
                        if page_proctabl:
                            urls_a.append(urlx)
                            print(f"{urlx} 可以访问")

                    except requests.RequestException as e:
                        pass
            except:
                print(f"{url_64} 访问失败")
                pass
        
        urls_a = set(urls_a)
        for a in urls_a:
            if count >= 3:
                continue
            else:
                urls_all.append(urls_a[a])
                count += 1
        return urls_all


urls_hn = ["changsha","hengyang"]
urls_sc = ['chengdu']
urls_bj = ["beijing"]

tf_hn = TextFileReader("hunan.txt")
tf_sc = TextFileReader("sichuan.txt")
tf_bj = TextFileReader("beijing.txt")
channelsx_hn = tf_hn.read_data()
channelsx_sc = tf_sc.read_data()
channelsx_bj = tf_bj.read_data()

u_hn = GetChannel(urls_hn)
urls_hn_all = set(u_hn.get_channel())
u_sc = GetChannel(urls_sc)
urls_sc_all = set(u_sc.get_channel())

u_bj = GetChannel(urls_bj, "China Unicom Beijing Province Network")
urls_bj_all = set(u_bj.get_channel())

results = []
channel = []
resultsx = []
resultxs = []
error_channels = []

def get_channel(urls, channels):
    for urlx in urls:
        for a in channels:
            channel = [f'{a.name},{a.url.replace("http://8.8.8.8:8", urlx)}']
            results.extend(channel)

    return results
            
results.extend(set(get_channel(urls_hn_all, channelsx_hn)))  # 去重得到唯一的URL列表
results.extend(set(get_channel(urls_sc_all, channelsx_sc)))  # 去重得到唯一的URL列表
results.extend(set(get_channel(urls_bj_all, channelsx_bj)))  # 去重得到唯一的URL列表

results = sorted(results) #排序

# 定义工作线程函数
def worker():
    while True:
        result = task_queue.get()
        channel_name, channel_url = result.split(',', 1)
        try:
            response = requests.get(channel_url, stream=True, timeout=3)
            if response.status_code == 200:
                result = channel_name, channel_url
                resultsx.append(result)
                numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
                print(
                    f"可用频道：{len(resultsx)} , 不可用频道：{len(error_channels)} 个 , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
            else:
                error_channels.append(result)
                numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
                print(
                    f"可用频道：{len(resultsx)} 个 , 不可用频道：{len(error_channels)} , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
        except:
            error_channels.append(result)
            numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
            print(
                f"可用频道：{len(resultsx)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")

        # 标记任务完成
        task_queue.task_done()


# 创建多个工作线程
num_threads = 15
for _ in range(num_threads):
    t = threading.Thread(target=worker, daemon=True)
    t.start()

# 添加下载任务到队列
for result in results:
    task_queue.put(result)

# 等待所有任务完成
task_queue.join()


def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字


for resulta in resultsx:
    channel_name, channel_url = resulta
    resultx = channel_name, channel_url
    resultxs.append(resultx)

# 对频道进行排序
resultxs.sort(key=lambda x: channel_key(x[0]))
# now_today = datetime.date.today()

result_counter = 15  # 每个频道需要的个数

with open("IPTV_ZB.txt", 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('央视频道,#genre#\n')
    for result in resultxs:
        channel_name, channel_url = result
        if 'CCTV' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('\n卫视频道,#genre#\n')
    for result in resultxs:
        channel_name, channel_url = result
        if '卫视' in channel_name or '凤凰' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('\n湖南频道,#genre#\n')
    for result in resultxs:
        channel_name, channel_url = result
        if '湖南' in channel_name or '长沙' in channel_name or '金鹰' in channel_name or '衡阳' in channel_name or '株洲' in channel_name or '张家界' in channel_name\
                or '娄底' in channel_name or '邵阳' in channel_name or '宁乡' in channel_name or '怀化' in channel_name or '岳阳' in channel_name or '郴州' in channel_name\
                or '常德' in channel_name or '永州' in channel_name or '浏阳' in channel_name or '益阳' in channel_name or  '安仁' in channel_name or '桂东' in channel_name\
                or '茶陵' in channel_name or '临澧' in channel_name or '武冈' in channel_name or '新化' in channel_name or '津市' in channel_name or '溆浦' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('\n其他频道,#genre#\n')
    for result in resultxs:
        channel_name, channel_url = result
        if 'CCTV' not in channel_name and '卫视' not in channel_name and '测试' not in channel_name and '湖南' not in \
            channel_name and '长沙' not in channel_name and '金鹰' not in channel_name and '凤凰' not in \
            channel_name and '衡阳' not in channel_name and '株洲' not in channel_name and '张家界' not in \
            channel_name and '娄底' not in channel_name and '邵阳' not in channel_name and '宁乡' not in \
            channel_name and '怀化' not in channel_name and '岳阳' not in channel_name and '郴州' not in \
            channel_name and '常德' not in channel_name and '永州' not in channel_name and '浏阳' not in \
            channel_name and '益阳' not in channel_name and '安仁' not in channel_name and '桂东' not in \
            channel_name and '茶陵' not in channel_name and '临澧' not in channel_name and '武冈' not in \
            channel_name and '新化' not in channel_name and '津市' not in channel_name and '溆浦' not in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

# 合并所有的txt文件
file_contents = []
file_paths = ["IPTV_ZB.txt", "GAT.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        file_contents.append(content)

    # 写入合并后的txt文件
with open("IPTV_ZB.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))
    # 写入更新日期时间
    # file.write(f"{now_today}更新,#genre#\n")
    # 获取当前时间
    now = datetime.now()          
    output.write(f"\n更新时间,#genre#\n")
    output.write(f"{now.strftime("%Y-%m-%d")},url\n")
    output.write(f"{now.strftime("%H:%M:%S")},url\n")

os.remove("DIYP-v4.txt")
os.remove("HK.txt")
os.remove("TW.txt")
os.remove("GAT.txt")

print(f"电视频道成功写入IPTV_ZB.txt")

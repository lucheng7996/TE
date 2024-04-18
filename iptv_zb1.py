import re
import base64
import requests
import threading
from queue import Queue

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

    def __init__(self, urls, org="Chinanet"):
        self.urls = urls
        self.org = org

    def get_channel(self):
        urls_a = []
        urls_all = []
        count = 0
        for url in self.urls:
            url_0 = str(base64.b64encode((f'"Server: udpxy" && region="{url}" && org="{self.org}"').encode("utf-8")),
                        "utf-8")
            url_64 = f'https://fofa.info/result?qbase64={url_0}'
            print(url_64)
            try:
                response = requests.get(url_64, headers=headers)
                page_content = response.text
                pattern = r'href="(http://\d+\.\d+\.\d+\.\d+:\d+)"'
                page_urls = re.findall(pattern, page_content)
                for urlx in page_urls:
                    try:
                        response = requests.get(url=urlx + '/status', timeout=3)
                        response.raise_for_status()  # 返回状态码不是200异常
                        page_content = response.text
                        # pattern = r'class="proctabl"'
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

        # urls_a = list(urls_a)
        # urls_all = urls_a[:3]  #取3个IP用于返回
        index = 1
        urls_cunt = 3  # 取3个不同IP
        for i in urls_a:
            if i in urls_all:
                continue
            else:
                if index > urls_cunt:
                    continue
                else:
                    index += 1
                    urls_all.append(i)
        print(urls_all)
        return urls_all

# urls_hn = ["changsha","hengyang","zhuzhou"]
urls_hn = ["hunan"]

#urls_sc = ['sichuan']
#urls_bj = ["beijing"]
#urls_fj = ["fujian"]

tf_hn = TextFileReader("hunan.txt")
#tf_sc = TextFileReader("sichuan.txt")
#tf_bj = TextFileReader("beijing.txt")
#tf_fj = TextFileReader("fujian.txt")
channelsx_hn = tf_hn.read_data()
#channelsx_sc = tf_sc.read_data()
#channelsx_bj = tf_bj.read_data()
#channelsx_fj = tf_fj.read_data()

u_hn = GetChannel(urls_hn)
urls_hn_all = set(u_hn.get_channel())
#u_sc = GetChannel(urls_sc)
#urls_sc_all = set(u_sc.get_channel())

#u_bj = GetChannel(urls_bj, "China Unicom Beijing Province Network")
#urls_bj_all = set(u_bj.get_channel())

#u_fj = GetChannel(urls_fj)
#urls_fj_all = set(u_fj.get_channel())

results = []
channel = []
resultsx = []
resultxs = []
error_channels = []


def get_channel(urls, channels):
    for urlx in urls:
        for a in channels:
            channel = [f'{a.name},{a.url.replace("http://8.8.8.8:8", urlx)}']
            if channel not in results:
                results.extend(channel)

    return results



# results.extend(set(get_channel(urls_bj_all, channelsx_bj)))  # 去重得到唯一的URL列表
# results.extend(set(get_channel(urls_fj_all, channelsx_fj)))  # 去重得到唯一的URL列表
# results.extend(set(get_channel(urls_sc_all, channelsx_sc)))  # 去重得到唯一的URL列表
print(urls_hn_all)
results.extend(get_channel(urls_hn_all, channelsx_hn))  # 去重得到唯一的URL列表


#results = sorted(results) #排序

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
                    f"可用频道：{len(resultsx)} 个, 不可用频道：{len(error_channels)} 个 , 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
            else:
                error_channels.append(result)
                numberx = (len(resultsx) + len(error_channels)) / len(results) * 100
                print(
                    f"可用频道：{len(resultsx)} 个 , 不可用频道：{len(error_channels)} 个, 总频道：{len(results)} 个 ,总进度：{numberx:.2f} %。")
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

for resulta in resultsx:
    channel_name, channel_url = resulta
    resultx = channel_name, channel_url
    resultxs.append(resultx)

# 对频道进行排序
#resultxs.sort(key=lambda x: channel_key(x[0]))
# now_today = datetime.date.today()

result_counter = 8  # 每个频道需要的个数

with open("IPTV_HN.txt", 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('湖南电信,#genre#\n')
    for result in resultxs:
        channel_name, channel_url = result
        #if 'CCTV' in channel_name:
        if channel_name in channel_counters:
            if channel_counters[channel_name] >= result_counter:
                continue
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] += 1
        else:
            file.write(f"{channel_name},{channel_url}\n")
            channel_counters[channel_name] = 1
file.close()

print(f"电视频道成功写入IPTV_HN.txt")

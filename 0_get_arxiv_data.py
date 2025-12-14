import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime

def fetch_papers_by_exact_date(category, date_str, max_results=100, output_dir='./data/new_data'):
    """
    category: arxiv分类，如'cs.AI'
    date_str: 目标日期字符串，格式 'YYYY-MM-DD'
    max_results: 最大抓取论文数
    """
    base_url = "http://export.arxiv.org/api/query?"
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    start = 0
    fetched = 0
    results = []

    # 目标日期的开始和结束时间
    date_start = datetime.strptime(date_str, "%Y-%m-%d")
    date_end = date_start.replace(hour=23, minute=59, second=59)

    # 构造API中的日期范围，格式为：YYYYMMDDHHMM
    date_start_str = date_start.strftime("%Y%m%d0000")
    date_end_str = date_start.strftime("%Y%m%d2359")

    date_query = f"submittedDate:[{date_start_str} TO {date_end_str}]"
    query = f"cat:{category}+AND+{date_query}"

    print(f"开始抓取分类 {category}，日期 {date_str} 的论文，最多抓取 {max_results} 篇")

    while fetched < max_results:
        url = (f"{base_url}search_query={query}"
               f"&start={start}&max_results=100"
               f"&sortBy=submittedDate&sortOrder=descending")
        print(f"\n请求第 {start//100 + 1} 页，url: {url}")
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"HTTP状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"请求失败，内容前500字符:\n{response.text[:500]}")
                break

            root = ET.fromstring(response.content)
            entries = root.findall("atom:entry", ns)
            print(f"本页获取到论文数: {len(entries)}")
            if not entries:
                print("无更多论文，停止抓取。")
                break

            for entry in entries:
                published_str = entry.find("atom:published", ns).text.strip()
                published_dt = datetime.strptime(published_str[:10], "%Y-%m-%d")

                # 精确过滤当天论文
                if published_dt.date() == date_start.date():
                    title = entry.find("atom:title", ns).text.strip().replace('\n', ' ')
                    summary = entry.find("atom:summary", ns).text.strip().replace('\n', ' ')
                    link = entry.find("atom:id", ns).text.strip()
                    results.append(f"[{published_str}] {title}\n{link}\n{summary}\n")
                    fetched += 1
                    print(f"抓到第{fetched}篇: {title}")

                    if fetched >= max_results:
                        break
                else:
                    print(f"论文不在目标日期，跳过: {published_str}")

            start += 100
            print("-------- 等待2秒，继续下一页请求 --------")
            time.sleep(2)
        except Exception as e:
            print("异常:", e)
            break

    if results:
        filename = f"{output_dir}{category}_{date_str}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for item in results:
                f.write(item + '\n\n')
        print(f"已保存 {len(results)} 篇论文到文件: {filename}")
    else:
        print("没有抓取到任何论文。")


# # 这是取某个日期某个分区的，建议取ai分区的 ，其他分区很偏僻
# if __name__ == "__main__":
#     output_dir='./data/new_data'
#     fetch_papers_by_exact_date(
#         category="cs.AI",
#         date_str="2025-10-29",
#         max_results=1
#     )


import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime
import os

def fetch_papers_by_exact_date(category, date_str, max_results=100, output_dir='./'):
    """
    category: arxiv分类，如'cs.AI'
    date_str: 目标日期字符串，格式 'YYYY-MM-DD'
    max_results: 最大抓取论文数
    output_dir: 保存文件的目录，必须存在
    """
    base_url = "http://export.arxiv.org/api/query?"
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    start = 0
    fetched = 0
    results = []

    date_start = datetime.strptime(date_str, "%Y-%m-%d")

    date_start_str = date_start.strftime("%Y%m%d0000")
    date_end_str = date_start.strftime("%Y%m%d2359")

    date_query = f"submittedDate:[{date_start_str} TO {date_end_str}]"
    query = f"cat:{category}+AND+{date_query}"

    print(f"开始抓取分类 {category}，日期 {date_str} 的论文，最多抓取 {max_results} 篇")

    while fetched < max_results:
        url = (f"{base_url}search_query={query}"
               f"&start={start}&max_results=100"
               f"&sortBy=submittedDate&sortOrder=descending")
        print(f"\n请求第 {start//100 + 1} 页，url: {url}")
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"HTTP状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"请求失败，内容前500字符:\n{response.text[:500]}")
                break

            root = ET.fromstring(response.content)
            entries = root.findall("atom:entry", ns)
            print(f"本页获取到论文数: {len(entries)}")
            if not entries:
                print("无更多论文，停止抓取。")
                break

            for entry in entries:
                published_str = entry.find("atom:published", ns).text.strip()
                published_dt = datetime.strptime(published_str[:10], "%Y-%m-%d")

                if published_dt.date() == date_start.date():
                    title = entry.find("atom:title", ns).text.strip().replace('\n', ' ')
                    summary = entry.find("atom:summary", ns).text.strip().replace('\n', ' ')
                    link = entry.find("atom:id", ns).text.strip()
                    results.append(f"[{published_str}] {title}\n{link}\n{summary}\n")
                    fetched += 1
                    print(f"抓到第{fetched}篇: {title}")

                    if fetched >= max_results:
                        break
                else:
                    print(f"论文不在目标日期，跳过: {published_str}")

            start += 100
            print("-------- 等待2秒，继续下一页请求 --------")
            time.sleep(15)
        except Exception as e:
            print("异常:", e)
            break

    if results:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = os.path.join(output_dir, f"{category}_{date_str}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            for item in results:
                f.write(item + '\n\n')
        print(f"已保存 {len(results)} 篇论文到文件: {filename}")
    else:
        print("没有抓取到任何论文。")



# 这个是取所有的分区每个分区100个
if __name__ == "__main__":
    categories = [
        "cs.AI","cs.AR","cs.CC","cs.CE","cs.CL","cs.CR","cs.CV","cs.CY","cs.DB","cs.DC",
        "cs.DL","cs.DM","cs.DS","cs.ET","cs.FL","cs.GL","cs.GR","cs.GT","cs.HC","cs.IR",
        "cs.IT","cs.LG","cs.LO","cs.MA","cs.MM","cs.MS","cs.NA","cs.NE","cs.NI","cs.OH",
        "cs.OS","cs.PF","cs.PL","cs.RO","cs.SC","cs.SD","cs.SE","cs.SI","cs.SY"
    ]

    dates = ["2025-10-28", "2025-10-29"]
    output_dir = "data/new_data/"

    for date_str in dates:
        for category in categories:
            fetch_papers_by_exact_date(
                category=category,
                date_str=date_str,
                max_results=1,
                output_dir=output_dir
            )
# 将这个文件夹下面的文件按照categories相同的不同日期合成一个大文件
import logging
import json
import requests
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


class OpenAIChatbot:
    def __init__(self, max_tokens,
                 model='DeepSeek-V3-0324-jdcloud-iaas',
                 temperature=1,
                 api_key="ecf75959-048c1fde70ad"):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_response(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        logging.info(f"请求消息长度: {len(prompt)}")
        server = 'http://gpt-proxy.jd.com/v1/chat/completions'
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        json_data = json.dumps(data)
        header = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"Bearer {self.api_key}"
        }
        max_attempts = 2
        attempt = 0

        while attempt < max_attempts:
            try:
                reply = requests.post(url=server, data=json_data, headers=header, timeout=60)
                if reply.status_code == 200:
                    reply = reply.json()
                    reply_text = reply['choices'][0]['message']['content']
                    return reply_text
                else:
                    logging.warning(f"请求失败，状态码: {reply.status_code} 内容: {reply.text}")
            except Exception as err:
                logging.warning(f"第{attempt + 1}次请求异常: {err}")
                time.sleep(15)
            attempt += 1

        return "Sorry, I couldn't get a reply after multiple attempts"


THEME_INNOVATION_PROMPT_TEMPLATE = """
你是技术论文的分析助手，针对输入的论文标题与摘要，极度简洁地提取以下三点：
1. 主题（用一短语，技术方向/领域/核心内容）
2. 场景（简明扼要）
3. 创新点（不少于两个创新点，要求简明扼要，分点列出）

格式如下：
主题：xxx
场景：xxx
创新点：
- 创新点1
- 创新点2
...

输入如下：
标题：{title}
摘要：{abstract}
"""


def generate_theme_innovation(title, abstract, chatbot):
    prompt = THEME_INNOVATION_PROMPT_TEMPLATE.format(title=title, abstract=abstract)
    return chatbot.get_response(prompt)


def parse_json_line(line):
    try:
        obj = json.loads(line)
        return obj.get('title', ''), obj.get('abstract', '')
    except Exception as e:
        logging.warning(f"解析JSON行失败: {e}，内容: {line}")
        return '', ''


def parse_theme_innovation_result(text):
    """
    解析模型返回的文本，提取主题、场景和多点创新点
    """
    theme = ""
    scene = ""
    innovations = []

    lines = text.strip().splitlines()
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith("主题"):
            current_section = "theme"
            theme = line.split("：", 1)[-1].strip()
        elif line.startswith("场景"):
            current_section = "scene"
            scene = line.split("：", 1)[-1].strip()
        elif line.startswith("创新点"):
            current_section = "innovation"
        elif current_section == "innovation":
            # 过滤开头符号，保存创新点内容
            content = re.sub(r"^[-•]\s*", "", line)
            if content:
                innovations.append(content)
        else:
            pass

    return {
        "主题": theme,
        "场景": scene,
        "创新点": innovations
    }


def batch_generate_theme_innovation(data_lines, chatbot, max_num=None, max_workers=10):
    results = {}

    def process_line(line):
        title, abstract = parse_json_line(line)
        if not title or not abstract:
            return None, None

        try:
            result_text = generate_theme_innovation(title, abstract, chatbot)
            parsed_result = parse_theme_innovation_result(result_text)
            return title, parsed_result
        except Exception as e:
            logging.error(f"处理论文《{title}》时异常: {e}")
            return title, {"主题": "", "场景": "", "创新点": []}

    count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_title = {executor.submit(process_line, line): line for line in data_lines}
        for future in as_completed(future_to_title):
            title, info = future.result()
            if title and info:
                results[title] = info
            count += 1
            if max_num and count >= max_num:
                break
            if count % 10 == 0:
                logging.info(f"已分析论文数: {count}")
    return results


def read_data(file_path, num_lines=None):
    data_lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        if num_lines is None:
            for line in f:
                line = line.strip()
                if line:
                    data_lines.append(line)
        else:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                line = line.strip()
                if line:
                    data_lines.append(line)
    return data_lines

#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
#     input_path = "/Users/maoshanwen.1/PycharmProjects/AI-Paper-IDEA/new_data/merged_json/cs.DB_all.jsonl"
#     lines = read_data(input_path)
#
#     chatbot = OpenAIChatbot(max_tokens=4096)
#
#     results = batch_generate_theme_innovation(lines, chatbot, max_workers=2)
#
#     with open("theme_innovation_results.json", "w", encoding="utf-8") as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
#
#     logging.info("批量处理完成，结果已保存。")
import os

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_dir = "//data/new_data/merged_json"
    output_dir = "/new_data_result"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 初始化chatbot（全局一个实例即可）
    chatbot = OpenAIChatbot(max_tokens=4096)

    # 遍历输入目录下所有文件
    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        # 只处理文件，忽略子目录等
        if not os.path.isfile(input_path):
            logging.info(f"跳过非文件: {input_path}")
            continue

        logging.info(f"开始处理文件: {input_path}")

        # 读取文件内容（可加num_lines限制测试）
        lines = read_data(input_path)

        # 批量调用接口处理
        results = batch_generate_theme_innovation(lines, chatbot, max_workers=4)

        # 保存结果，文件名和输入文件名对应
        output_path = os.path.join(output_dir, f"{filename}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logging.info(f"文件处理完成，结果保存到: {output_path}")

    logging.info("所有文件处理完毕。")


#
#


import logging
import json
import re
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI  # 需pip安装 openai 包
os.environ["DEEPSEEK_API_KEY"] = "mmmmmmmmmmc"
class OpenAIChatbot:
    def __init__(self, max_tokens,
                 model='deepseek-chat',
                 temperature=1,
                 api_key=None,
                 base_url="https://api.deepseek.com"):
        if api_key is None:
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise ValueError("请通过环境变量 DEEPSEEK_API_KEY 设置API密钥")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_response(self, prompt):
        messages = [
            {"role": "system", "content": "你是技术论文的分析助手。"},
            {"role": "user", "content": prompt}
        ]
        logging.info(f"请求消息长度: {len(prompt)}")
        max_attempts = 2
        attempt = 0
        while attempt < max_attempts:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=False
                )
                reply_text = response.choices[0].message.content
                return reply_text
            except Exception as e:
                logging.warning(f"第{attempt + 1}次请求异常: {e}")
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
        return obj.get('title', ''), obj.get('abstract', ''),obj.get('decision', '')
    except Exception as e:
        logging.warning(f"解析JSON行失败: {e}，内容: {line}")
        return '', ''


def parse_theme_innovation_result(text):
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
            content = re.sub(r"^[-•]\s*", "", line)
            if content:
                innovations.append(content)
    return {
        "主题": theme,
        "场景": scene,
        "创新点": innovations
    }


def batch_generate_theme_innovation(data_lines, chatbot, max_num=None, max_workers=10):
    results = {}

    def process_line(line):
        title, abstract, decision = parse_json_line(line)
        if not title or not abstract:
            return None, None

        try:
            result_text = generate_theme_innovation(title, abstract, chatbot)
            parsed_result = parse_theme_innovation_result(result_text)
            # 加decision
            parsed_result["decision"] = decision
            return title, parsed_result
        except Exception as e:
            logging.error(f"处理论文《{title}》时异常: {e}")
            return title, {"主题": "", "场景": "", "创新点": [], "decision": decision}

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




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_dir = "//data/old_data"
    output_dir = "//old_data_result"

    os.makedirs(output_dir, exist_ok=True)

    chatbot = OpenAIChatbot(max_tokens=4096)

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            logging.info(f"跳过非文件: {input_path}")
            continue

        logging.info(f"开始处理文件: {input_path}")
        lines = read_data(input_path)
        print("lines :",lines)

        results = batch_generate_theme_innovation(lines, chatbot, max_workers=4)

        output_path = os.path.join(output_dir, f"{filename}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logging.info(f"文件处理完成，结果保存到: {output_path}")

    logging.info("所有文件处理完毕。")



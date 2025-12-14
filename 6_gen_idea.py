
import logging
import json
import re
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI  # 需pip安装 openai 包
os.environ["DEEPSEEK_API_KEY"] = "sk-8f291d795e7447fda8b6173ecdfb49dc"

# 文件加载（可以控制数据数量）
def load_json_dict(filepath, max_items=None):
    """
    加载完整JSON文件，内容是一个大字典。
    :param filepath: 文件路径
    :param max_items: 最大返回条目数，None表示全部返回
    :return: 截取后的子字典
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if max_items is None:
        return data

    # 只取前max_items条
    keys = list(data.keys())[:max_items]
    filtered_data = {k: data[k] for k in keys}
    return filtered_data




#  构建提示工程模板THEME_INNOVATION_PROMPT_TEMPLATE
THEME_INNOVATION_PROMPT_TEMPLATE = """
你是一名AI科研人员，负责基于历史研究条目，结合“量化（quantization）”技术，提出一个具有突破性吸引力的新场景，以及至少两条互不重合的创新点。

请严格遵守以下格式输出，格式必须是 JSON：
{{
  "标题":"",
  "主题": "",
  "场景": "",
  "创新点": ["", ""]
}}

要求：  
1. 新场景需具有高度吸引力和现实意义，比如“单次数据注入刷新世界纪录”等；  
2. 两条创新点必须基于量化技术，且技术方案之间互不重合，体现多角度创新；  
3. 创新点要有具体技术亮点，避免泛泛而谈。

---

示例1：

旧标题：Catastrophic Failure of LLM Unlearning via Quantization  
旧主题：大语言模型遗忘机制  
旧场景：量化操作导致已遗忘知识恢复  
旧创新点：
1. 发现量化技术可恢复模型"遗忘"内容（4位量化使知识保留率从21%升至83%）  
2. 提出量化鲁棒的遗忘策略以缓解该问题  

{{
  "标题":"基于量化的单次数据注入实现世界纪录级知识更新",
  "主题": "大语言模型动态知识更新",
  "场景": "结合高精度动态量化技术，实现大模型单次数据注入后即时更新并查询最新世界纪录，无需多轮微调或重训练。",
  "创新点": [
    "设计基于动态比特分配的局部量化重组技术，仅针对更新知识模块实施高精度量化，保证更新效率与知识完整性。",
    "提出量化扰动鲁棒机制，通过对量化引入的噪声建模，保障单次注入操作对模型整体性能影响最小化，确保模型稳定。"
  ]
}}
---

示例2：

旧标题：One Step Diffusion via Shortcut Models  
旧主题：生成模型加速采样  
旧场景：图像生成中扩散模型采样速度慢、计算成本高的问题  
旧创新点：
1. 引入单网络单阶段训练框架，支持单步或多步采样  
2. 通过同时输入噪声水平和步长参数实现生成过程跳跃  

{{
  "标题":"量化驱动的端侧秒级个性化图像生成",
  "主题": "轻量级生成模型优化",
  "场景": "面向手机端，结合量化技术实现秒级个性化头像生成，完全无需依赖云端。  ",
  "创新点": ["利用超低比特动态权重量化，分层压缩模型各部分参数，极大降低内存和计算需求。", "创新量化感知输入适配机制，根据用户输入特征动态调整量化精度，保障生成效果和个性化表达。"]
}}
---

请根据下面旧条目，结合示例，输出新的创新内容(不需要其他多余文字)：

旧标题：{title}  
旧主题：{theme}  
旧场景：{scene}  
旧创新点：  
{innovations}  
"""

#
#


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
            {"role": "system", "content": "你是AI科研人员。"},
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



#  todo 构造提示给大模型处理
def generate_theme_innovation(old_title, old_theme, old_scene, old_innovation_list, chatbot):
    # 把创新点列表拼成多行字符串
    innovations_str = ""
    for i, item in enumerate(old_innovation_list, 1):
        # 保证每条创新点格式化成一行，例如 "1. xxx"
        innovations_str += f"{i}. {item}\n"

    prompt = THEME_INNOVATION_PROMPT_TEMPLATE.format(
        title=old_title,
        theme=old_theme,
        scene=old_scene,
        innovations=innovations_str.strip()  # 去除末尾多余换行
    )

    return chatbot.get_response(prompt)


def parse_model_output(text):
    """
    解析模型返回的json格式字符串为python对象，容错处理。
    如果传入已经是dict类型，直接返回。
    """
    if isinstance(text, dict):
        return text

    if text is None:
        return {"解析错误": "模型返回None值"}

    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except Exception as e:
                logging.warning(f"JSON解析失败: {e}，返回原始文本")
                return {"解析错误": f"JSON解析失败: {e}", "原始返回": text}
        else:
            logging.warning("未匹配到JSON内容，返回原始文本")
            return {"解析错误": "未匹配到JSON对象", "原始返回": text}

def batch_generate_theme_innovation(data_lines, chatbot, max_num=None, max_workers=10):
    results = {}
    # 限制处理条数
    items = list(data_lines.items())
    if max_num is not None:
        items = items[:max_num]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {}
        for key, value in items:
            old_title = key
            old_theme = value.get("主题", "")
            old_scene = value.get("场景", "")
            old_innovation_list = value.get("创新点", [])
            future = executor.submit(generate_theme_innovation, old_title, old_theme, old_scene, old_innovation_list, chatbot)
            future_to_key[future] = key

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                raw_text = future.result()

                parsed_result = parse_model_output(raw_text)
                results[key] = parsed_result
            except Exception as e:
                logging.error(f"处理条目 {key} 出错: {e}")
                results[key] = {
                    "错误": str(e)
                }

    return results


if __name__ == "__main__":
    filepath = "//old_data_result/ICMLcc_2025_Conference_papers_reviews.jsonl.json"
    max_num = 2  # 例如只加载5条数据
    data = load_json_dict(filepath)
    print(f"成功加载 {len(data)} 条数据")

    chatbot = OpenAIChatbot(max_tokens=4096)
    print("初始化成功")
    raw_results = batch_generate_theme_innovation(data, chatbot, max_workers=10)
    print("raw_results ",raw_results )
    # 解析每条返回的文本，转成结构化dict
    results = {}
    for title, text in raw_results.items():
        parsed = parse_model_output(text)
        results[title] = parsed

    # 保存到文件
    save_path = '//old_data_result/idea/ICML2025_result.json'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"结果已保存到 {save_path}")






# todo  文件保存到
# /Users/maoshanwen.1/PycharmProjects/AI-Paper-IDEA/old_data_result/ICLR2025_result.json
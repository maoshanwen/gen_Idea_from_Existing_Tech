

import os
import re
import json

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 以两个及以上换行符分割条目
    entries = re.split(r'\n\s*\n', content.strip())

    json_lines = []
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) < 3:
            continue  # 格式异常跳过

        title_line = lines[0]
        abstract = ' '.join(lines[2:]).strip()
        m = re.match(r'\[.*?\]\s*(.*)', title_line)
        if not m:
            continue
        title = m.group(1).strip()
        if ': ' in title:
            title = title.split(': ', 1)[1]

        json_obj = {"title": title, "abstract": abstract}
        json_lines.append(json.dumps(json_obj, ensure_ascii=False))

    with open(output_path, 'w', encoding='utf-8') as out:
        for line in json_lines:
            out.write(line + "\n")

def batch_process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if not filename.endswith('.txt'):
            continue
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.txt', '.jsonl'))
        process_file(input_path, output_path)
        print(f"Processed: {filename} -> {output_path}")

if __name__ == '__main__':
    input_folder = "/Users/maoshanwen.1/PycharmProjects/AI-Paper-IDEA/data/new_data/merged"
    output_folder = "/Users/maoshanwen.1/PycharmProjects/AI-Paper-IDEA/data/new_data/merged_json"
    batch_process_folder(input_folder, output_folder)

#
# todo 将/Users/maoshanwen.1/PycharmProjects/AI-Paper-IDEA/new_data/merged的每个文件的每个数据修改成json格式：每条数据一个标题一个摘要{"title":,"abstract",}
# 每个文件数据格式如下
# [2025-10-24T12:49:38Z] GreenMalloc: Allocator Optimisation for Industrial Workloads
# http://arxiv.org/abs/2510.21405v1
# We present GreenMalloc, a multi objective search-based framework for automatically configuring memory allocators. Our approach uses NSGA II and rand_malloc as a lightweight proxy benchmarking tool. We efficiently explore allocator parameters from execution traces and transfer the best configurations to gem5, a large system simulator, in a case study on two allocators: the GNU C/CPP compiler's glibc malloc and Google's TCMalloc. Across diverse workloads, our empirical results show up to 4.1 percantage reduction in average heap usage without loss of runtime efficiency; indeed, we get a 0.25 percantage reduction.
#
#
# [2025-10-24T01:41:43Z] Accelerating Mobile Inference through Fine-Grained CPU-GPU Co-Execution
# http://arxiv.org/abs/2510.21081v1
# Deploying deep neural networks on mobile devices is increasingly important but remains challenging due to limited computing resources. On the other hand, their unified memory architecture and narrower gap between CPU and GPU performance provide an opportunity to reduce inference latency by assigning tasks to both CPU and GPU. The main obstacles for such collaborative execution are the significant synchronization overhead required to combine partial results, and the difficulty of predicting execution times of tasks assigned to CPU and GPU (due to the dynamic selection of implementations and parallelism level). To overcome these obstacles, we propose both a lightweight synchronization mechanism based on OpenCL fine-grained shared virtual memory (SVM) and machine learning models to accurately predict execution times. Notably, these models capture the performance characteristics of GPU kernels and account for their dispatch times. A comprehensive evaluation on four mobile platforms shows that our approach can quickly select CPU-GPU co-execution strategies achieving up to 1.89x speedup for linear layers and 1.75x speedup for convolutional layers (close to the achievable maximum values of 2.01x and 1.87x, respectively, found by exhaustive grid search on a Pixel~5 smartphone).
#

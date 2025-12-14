import os

categories = [
    "cs.AI","cs.AR","cs.CC","cs.CE","cs.CL","cs.CR","cs.CV","cs.CY","cs.DB","cs.DC",
    "cs.DL","cs.DM","cs.DS","cs.ET","cs.FL","cs.GL","cs.GR","cs.GT","cs.HC","cs.IR",
    "cs.IT","cs.LG","cs.LO","cs.MA","cs.MM","cs.MS","cs.NA","cs.NE","cs.NI","cs.OH",
    "cs.OS","cs.PF","cs.PL","cs.RO","cs.SC","cs.SD","cs.SE","cs.SI","cs.SY"
]

def merge_files_by_category(input_dir, output_dir, categories):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for category in categories:
        # 找到所有匹配该category的文件
        matched_files = [f for f in os.listdir(input_dir) if f.startswith(category + "_") and f.endswith(".txt")]
        if not matched_files:
            print(f"警告：目录中未找到类别 {category} 的文件，跳过。")
            continue

        output_path = os.path.join(output_dir, f"{category}_all.txt")
        with open(output_path, "w", encoding="utf-8") as outfile:
            for filename in sorted(matched_files):
                filepath = os.path.join(input_dir, filename)
                with open(filepath, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n")  # 文件间添加空行隔开
        print(f"已合并类别 {category} 的 {len(matched_files)} 个文件，输出到 {output_path}")

if __name__ == "__main__":
    input_dir = "//data/new_data"
    output_dir = "//data/new_data/merged"

    merge_files_by_category(input_dir, output_dir, categories)

import os
import time


def generate_code_markdown(root_dir, output_file, extensions):
    # 1. 配置：要忽略的文件夹
    exclude_dirs = {
        '.git', '.vscode', '__pycache__', 'build', 'dist',
        'venv', 'node_modules', '.idea', '.settings'
    }

    # 2. 配置：要忽略的具体文件名
    exclude_files = {
        'code_to_md.py',  # 忽略脚本自身
        'project_code_context.md',  # 忽略输出文件
        'temp_test.py'  # 举例：忽略临时的测试文件
    }

    total_files = 0
    total_lines = 0
    total_chars = 0
    file_list = []

    # 预扫描获取合法文件
    for root, dirs, files in os.walk(root_dir):
        # 过滤文件夹
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            # 过滤后缀名
            if not any(file.endswith(ext) for ext in extensions):
                continue

            # 过滤特定文件名
            if file in exclude_files:
                continue

            # 过滤以特定字符开头的文件（可选，例如忽略所有以 'aaa' 开头的文件）
            if file.startswith('aaa'):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_dir)
            file_list.append((full_path, rel_path))
            total_files += 1

    # 开始写入 Markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Project Source Code Archive\n")
        f.write(f"- **Generated at**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Root**: `{os.path.abspath(root_dir)}`\n\n")

        # 项目结构树（排除掉忽略的文件）
        f.write("## Project Structure\n```text\n")
        # 简单模拟树状结构
        for _, rel_path in file_list:
            f.write(f"{rel_path}\n")
        f.write("```\n\n---\n\n")

        # 源代码内容
        f.write("## Source Code Content\n\n")
        for full_path, rel_path in file_list:
            f.write(f"### File: {rel_path}\n")

            ext = os.path.splitext(rel_path)[1][1:]
            lang = 'cpp' if ext in ['cpp', 'h', 'c'] else 'python'

            f.write(f"```{lang}\n")
            try:
                with open(full_path, 'r', encoding='utf-8') as code_f:
                    content = code_f.read()
                    f.write(content)
                    total_lines += len(content.splitlines())
                    total_chars += len(content)
            except Exception as e:
                f.write(f"// Error reading file: {e}")
            f.write("\n```\n\n")

    # 计算 Token (Gemini 估算：1 token ≈ 4 字符)
    estimated_tokens = total_chars // 4

    print(f"Successfully generated {output_file}")
    print(f"Summary:")
    print(f"- Total Files Included: {total_files}")
    print(f"- Total Lines of Code: {total_lines}")
    print(f"- Estimated Tokens: ~{estimated_tokens}")


if __name__ == "__main__":
    # 执行参数
    generate_code_markdown(
        root_dir=".",
        output_file="project_code_context.md",
        extensions=['.py', '.c', '.cpp', '.h']
    )
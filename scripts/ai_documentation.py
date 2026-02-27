#!/usr/bin/env python3
"""
AI文档生成脚本
自动为风荷载计算项目生成文档
"""

import os
import sys
import json
from pathlib import Path
from huggingface_ai_helper import HuggingFaceAI

def find_python_files(directory="src"):
    """查找Python文件"""
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    return python_files

def read_file_content(filepath):
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败 {filepath}: {e}")
        return ""

def determine_doc_type(filename, content):
    """确定文档类型"""
    if "__init__.py" in str(filename):
        return "module"
    elif "class " in content and "def " in content:
        return "class"
    elif "def " in content:
        return "function"
    else:
        return "module"

def generate_documentation(ai_helper, filepath, content, doc_type):
    """生成文档"""
    print(f"生成 {doc_type} 文档: {filepath}")
    
    # 生成文档
    documentation = ai_helper.generate_documentation(content, doc_type)
    
    # 保存到docs目录
    docs_dir = Path("docs") / filepath.parent.relative_to("src")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    docs_file = docs_dir / f"{filepath.stem}.md"
    
    with open(docs_file, 'w', encoding='utf-8') as f:
        f.write(f"# {filepath.name} 文档\n\n")
        f.write(f"**文件路径**: `{filepath}`\n")
        f.write(f"**文档类型**: {doc_type}\n\n")
        f.write("---\n\n")
        f.write(documentation)
    
    print(f"✅ 文档已保存: {docs_file}")
    return docs_file

def generate_module_overview(ai_helper, module_files):
    """生成模块概览"""
    print("生成模块概览...")
    
    module_info = []
    for filepath in module_files:
        content = read_file_content(filepath)
        if content:
            doc_type = determine_doc_type(filepath, content)
            module_info.append({
                "file": str(filepath),
                "type": doc_type,
                "size": len(content)
            })
    
    # 生成概览文档
    prompt = f"""请为以下Python模块生成中文概览文档：

模块信息：
{json.dumps(module_info, indent=2, ensure_ascii=False)}

项目：风荷载计算工具

要求：
1. 项目整体介绍
2. 模块结构说明
3. 主要功能概述
4. 使用指南
5. 技术特点

请用专业的Markdown格式。"""
    
    overview = ai_helper.query(prompt, max_length=1000)
    
    if isinstance(overview, list) and len(overview) > 0:
        overview_text = overview[0].get("generated_text", "")
    elif isinstance(overview, dict) and "generated_text" in overview:
        overview_text = overview["generated_text"]
    else:
        overview_text = str(overview)
    
    # 保存概览
    overview_file = Path("docs") / "OVERVIEW.md"
    overview_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(overview_file, 'w', encoding='utf-8') as f:
        f.write("# 风荷载计算工具 - 项目概览\n\n")
        f.write(overview_text)
    
    print(f"✅ 项目概览已保存: {overview_file}")
    return overview_file

def main():
    """主函数"""
    print("=" * 60)
    print("AI文档生成工具 - 风荷载计算项目")
    print("=" * 60)
    
    # 检查环境变量
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("❌ 错误：未设置HF_TOKEN环境变量")
        print("请在GitHub Secrets中配置HF_TOKEN")
        sys.exit(1)
    
    # 创建AI助手
    try:
        ai = HuggingFaceAI(api_token=hf_token)
        print("✅ Hugging Face AI助手已初始化")
    except Exception as e:
        print(f"❌ AI助手初始化失败: {e}")
        sys.exit(1)
    
    # 查找Python文件
    print("\n🔍 查找Python文件...")
    python_files = find_python_files("src")
    
    if not python_files:
        print("❌ 未找到Python文件，请检查src目录")
        # 尝试当前目录
        python_files = find_python_files(".")
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 生成文档
    generated_files = []
    for filepath in python_files:
        content = read_file_content(filepath)
        if content:
            doc_type = determine_doc_type(filepath, content)
            try:
                docs_file = generate_documentation(ai, filepath, content, doc_type)
                generated_files.append(docs_file)
            except Exception as e:
                print(f"❌ 生成文档失败 {filepath}: {e}")
    
    # 生成项目概览
    if python_files:
        try:
            overview_file = generate_module_overview(ai, python_files)
            generated_files.append(overview_file)
        except Exception as e:
            print(f"❌ 生成概览失败: {e}")
    
    # 生成索引
    print("\n📋 生成文档索引...")
    index_file = Path("docs") / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# 风荷载计算工具 - 文档索引\n\n")
        f.write("> 本文档由AI自动生成\n\n")
        
        f.write("## 项目文档\n\n")
        f.write("### 概览\n")
        f.write("- [项目概览](OVERVIEW.md)\n\n")
        
        f.write("### 模块文档\n")
        for docs_file in generated_files:
            if docs_file.name != "OVERVIEW.md" and docs_file.name != "README.md":
                rel_path = docs_file.relative_to("docs")
                f.write(f"- [{rel_path}]({rel_path})\n")
    
    print(f"\n✅ 文档生成完成！")
    print(f"   生成文档数: {len(generated_files)}")
    print(f"   文档目录: docs/")
    print(f"   索引文件: docs/README.md")
    
    # 生成报告
    report = {
        "timestamp": os.path.getmtime(__file__),
        "files_processed": len(python_files),
        "docs_generated": len(generated_files),
        "docs_files": [str(f) for f in generated_files]
    }
    
    with open("docs_generation_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 报告已保存: docs_generation_report.json")

if __name__ == "__main__":
    main()
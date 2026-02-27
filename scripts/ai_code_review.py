#!/usr/bin/env python3
"""
AI代码审查脚本
自动审查风荷载计算项目的代码质量
"""

import os
import sys
import json
import ast
from pathlib import Path
from huggingface_ai_helper import HuggingFaceAI

def find_changed_files():
    """查找更改的文件（用于PR审查）"""
    # 这里简化处理，审查所有Python文件
    return find_python_files("src")

def find_python_files(directory="src"):
    """查找Python文件"""
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    return python_files

def analyze_code_structure(filepath, content):
    """分析代码结构"""
    try:
        tree = ast.parse(content)
        
        # 收集信息
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "args": len(node.args.args),
                    "lineno": node.lineno,
                    "docstring": ast.get_docstring(node)
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "docstring": ast.get_docstring(node)
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return {
            "file": str(filepath),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "line_count": len(content.splitlines()),
            "char_count": len(content)
        }
    except SyntaxError as e:
        return {
            "file": str(filepath),
            "error": f"语法错误: {e}",
            "line_count": len(content.splitlines())
        }

def perform_ai_code_review(ai_helper, filepath, content, analysis):
    """执行AI代码审查"""
    print(f"审查代码: {filepath}")
    
    # 准备审查提示
    prompt = f"""请对以下Python代码进行专业代码审查：

文件: {filepath}

代码内容:
```python
{content[:2000]}  # 限制长度
```

代码分析:
{json.dumps(analysis, indent=2, ensure_ascii=False)}

审查要求:
1. 代码质量评估
2. 潜在问题发现
3. 性能优化建议
4. 安全性检查
5. 可读性改进
6. 规范符合性（PEP 8）
7. 具体修改建议

请用中文回复，格式：
- ✅ 优点
- ⚠️  问题
- 🔧 建议
- 📝 具体修改

针对风荷载计算项目的特殊性，请特别关注：
- 数值计算准确性
- 错误处理完整性
- 文档完整性
- 工程应用可靠性"""
    
    # 调用AI审查
    review = ai_helper.query(prompt, max_length=1500)
    
    if isinstance(review, list) and len(review) > 0:
        review_text = review[0].get("generated_text", "")
    elif isinstance(review, dict) and "generated_text" in review:
        review_text = review["generated_text"]
    else:
        review_text = str(review)
    
    return {
        "file": str(filepath),
        "analysis": analysis,
        "review": review_text,
        "has_issues": "⚠️" in review_text or "❌" in review_text or "问题" in review_text
    }

def generate_review_summary(ai_helper, all_reviews):
    """生成审查总结"""
    print("生成审查总结...")
    
    summary_data = {
        "total_files": len(all_reviews),
        "files_with_issues": sum(1 for r in all_reviews if r["has_issues"]),
        "total_functions": sum(len(r["analysis"].get("functions", [])) for r in all_reviews),
        "total_classes": sum(len(r["analysis"].get("classes", [])) for r in all_reviews),
        "reviews": all_reviews
    }
    
    # 生成总结提示
    prompt = f"""请基于以下代码审查结果生成项目总结：

审查概况:
- 审查文件数: {summary_data['total_files']}
- 存在问题文件: {summary_data['files_with_issues']}
- 总函数数: {summary_data['total_functions']}
- 总类数: {summary_data['total_classes']}

详细审查结果:
{json.dumps([r for r in all_reviews if r['has_issues']], indent=2, ensure_ascii=False)}

总结要求:
1. 项目整体代码质量评估
2. 主要问题分类
3. 优先级建议（高/中/低）
4. 改进路线图
5. 最佳实践建议

请用专业的技术报告格式，适合项目管理者阅读。"""
    
    summary = ai_helper.query(prompt, max_length=1000)
    
    if isinstance(summary, list) and len(summary) > 0:
        summary_text = summary[0].get("generated_text", "")
    elif isinstance(summary, dict) and "generated_text" in summary:
        summary_text = summary["generated_text"]
    else:
        summary_text = str(summary)
    
    return {
        "summary": summary_text,
        "data": summary_data
    }

def save_review_results(all_reviews, summary):
    """保存审查结果"""
    # 保存详细审查结果
    reviews_dir = Path("code_reviews")
    reviews_dir.mkdir(exist_ok=True)
    
    # 保存每个文件的审查
    for review in all_reviews:
        filename = Path(review["file"]).name.replace(".py", "_review.md")
        review_file = reviews_dir / filename
        
        with open(review_file, 'w', encoding='utf-8') as f:
            f.write(f"# 代码审查报告: {review['file']}\n\n")
            f.write(f"**审查时间**: {os.path.getmtime(__file__)}\n")
            f.write(f"**文件大小**: {review['analysis'].get('line_count', 0)} 行\n\n")
            f.write("---\n\n")
            f.write(review["review"])
    
    # 保存总结
    summary_file = reviews_dir / "SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# 代码审查项目总结\n\n")
        f.write(summary["summary"])
    
    # 保存JSON数据
    data_file = reviews_dir / "review_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": summary,
            "reviews": all_reviews
        }, f, indent=2, ensure_ascii=False)
    
    # 生成GitHub评论格式
    if os.getenv("GITHUB_ACTIONS"):
        comments = []
        for review in all_reviews:
            if review["has_issues"]:
                # 简化评论内容
                comment = {
                    "path": review["file"],
                    "line": 1,  # 默认第一行
                    "body": f"## AI代码审查发现的问题\n\n{review['review'][:500]}..."
                }
                comments.append(comment)
        
        with open("ai_review_comments.json", 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
    
    return reviews_dir

def main():
    """主函数"""
    print("=" * 60)
    print("AI代码审查工具 - 风荷载计算项目")
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
        print("⚠️  未找到src目录，尝试当前目录")
        python_files = find_python_files(".")
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 执行代码审查
    all_reviews = []
    for filepath in python_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分析代码结构
            analysis = analyze_code_structure(filepath, content)
            
            # AI审查
            review = perform_ai_code_review(ai, filepath, content, analysis)
            all_reviews.append(review)
            
            if review["has_issues"]:
                print(f"⚠️  发现问题: {filepath}")
            else:
                print(f"✅ 通过审查: {filepath}")
                
        except Exception as e:
            print(f"❌ 审查失败 {filepath}: {e}")
    
    # 生成总结
    if all_reviews:
        summary = generate_review_summary(ai, all_reviews)
        
        # 保存结果
        output_dir = save_review_results(all_reviews, summary)
        
        print(f"\n✅ 代码审查完成！")
        print(f"   审查文件数: {len(all_reviews)}")
        print(f"   发现问题文件: {sum(1 for r in all_reviews if r['has_issues'])}")
        print(f"   输出目录: {output_dir}/")
        print(f"   总结文件: {output_dir}/SUMMARY.md")
        
        # 显示关键问题
        issues = [r for r in all_reviews if r["has_issues"]]
        if issues:
            print("\n📋 关键问题文件:")
            for issue in issues[:5]:  # 显示前5个
                print(f"   - {issue['file']}")
    else:
        print("❌ 未完成任何代码审查")

if __name__ == "__main__":
    main()
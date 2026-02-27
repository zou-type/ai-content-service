#!/usr/bin/env python3
"""
生成风荷载计算示例和报告
"""

import os
import json
import sys
from pathlib import Path
from huggingface_ai_helper import HuggingFaceAI

def create_example_calculations():
    """创建计算示例"""
    examples = [
        {
            "name": "高层办公楼风荷载计算",
            "building_type": "办公楼",
            "height": 150,  # 米
            "width": 40,
            "depth": 30,
            "terrain_category": "C",
            "location": "上海",
            "code_standard": "GB50009"
        },
        {
            "name": "住宅楼风荷载计算",
            "building_type": "住宅",
            "height": 80,
            "width": 25,
            "depth": 20,
            "terrain_category": "B",
            "location": "北京",
            "code_standard": "GB50009"
        },
        {
            "name": "工业厂房风荷载计算",
            "building_type": "厂房",
            "height": 20,
            "width": 60,
            "depth": 40,
            "terrain_category": "A",
            "location": "广州",
            "code_standard": "GB50009"
        }
    ]
    
    return examples

def simulate_calculation_results(building_params):
    """模拟计算结果（实际项目应使用真实计算）"""
    height = building_params["height"]
    terrain = building_params["terrain_category"]
    
    # 简化计算逻辑
    if terrain == "A":
        height_factor = 1.0
    elif terrain == "B":
        height_factor = 1.2
    elif terrain == "C":
        height_factor = 1.4
    else:  # D
        height_factor = 1.6
    
    # 基本风压（简化）
    basic_wind_pressure = 0.5 * 1.25 * (30 ** 2) / 1000  # 30m/s风速
    
    # 体型系数（简化）
    shape_factor = 1.3
    
    # 计算风压
    wind_pressure = basic_wind_pressure * height_factor * shape_factor
    
    # 总风荷载
    area = building_params["width"] * building_params["height"]
    total_wind_load = wind_pressure * area
    
    return {
        "basic_wind_pressure": round(basic_wind_pressure, 3),
        "height_factor": round(height_factor, 2),
        "shape_factor": shape_factor,
        "wind_pressure": round(wind_pressure, 3),
        "building_area": round(area, 1),
        "total_wind_load": round(total_wind_load, 1),
        "units": {
            "pressure": "kN/m²",
            "load": "kN",
            "area": "m²"
        }
    }

def generate_ai_report(ai_helper, building_params, results, code_standard):
    """生成AI报告"""
    print(f"生成报告: {building_params['name']}")
    
    report = ai_helper.generate_calculation_report(
        building_params, 
        results, 
        code_standard
    )
    
    return report

def save_report(building_name, report_content, results_data):
    """保存报告"""
    # 创建reports目录
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 生成文件名
    safe_name = building_name.replace(" ", "_").replace("/", "_")
    report_file = reports_dir / f"{safe_name}_report.md"
    
    # 保存报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# {building_name} - 风荷载计算报告\n\n")
        f.write("> 本文档由AI自动生成\n\n")
        f.write(report_content)
    
    # 保存原始数据
    data_file = reports_dir / f"{safe_name}_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({
            "building_params": building_params,
            "results": results_data,
            "generated_at": os.path.getmtime(__file__)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 报告已保存: {report_file}")
    return report_file

def main():
    """主函数"""
    print("=" * 60)
    print("风荷载计算示例生成器")
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
    
    # 创建计算示例
    print("\n🔢 创建计算示例...")
    examples = create_example_calculations()
    print(f"创建了 {len(examples)} 个计算示例")
    
    # 生成报告
    generated_reports = []
    for example in examples:
        try:
            # 模拟计算
            results = simulate_calculation_results(example)
            
            # 生成AI报告
            report_content = generate_ai_report(
                ai, 
                example, 
                results, 
                example["code_standard"]
            )
            
            # 保存报告
            report_file = save_report(
                example["name"], 
                report_content, 
                results
            )
            
            generated_reports.append({
                "example": example["name"],
                "report_file": str(report_file),
                "results": results
            })
            
        except Exception as e:
            print(f"❌ 生成报告失败 {example['name']}: {e}")
    
    # 生成汇总报告
    if generated_reports:
        print("\n📊 生成汇总报告...")
        
        summary_data = {
            "total_examples": len(examples),
            "successful_reports": len(generated_reports),
            "reports": generated_reports,
            "generated_at": os.path.getmtime(__file__)
        }
        
        summary_file = Path("reports") / "SUMMARY.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# 风荷载计算示例汇总\n\n")
            f.write(f"**生成时间**: {summary_data['generated_at']}\n")
            f.write(f"**总示例数**: {summary_data['total_examples']}\n")
            f.write(f"**成功报告**: {summary_data['successful_reports']}\n\n")
            
            f.write("## 报告列表\n\n")
            for report in generated_reports:
                rel_path = Path(report["report_file"]).relative_to("reports")
                f.write(f"### {report['example']}\n")
                f.write(f"- 报告文件: [{rel_path}]({rel_path})\n")
                f.write(f"- 总风荷载: {report['results']['total_wind_load']} kN\n")
                f.write(f"- 风压: {report['results']['wind_pressure']} kN/m²\n\n")
        
        # 保存JSON数据
        with open("reports/summary_data.json", 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 汇总报告已保存: {summary_file}")
        print(f"📁 所有报告保存在: reports/")
        print(f"📄 报告数量: {len(generated_reports)}")
    else:
        print("❌ 未生成任何报告")
        sys.exit(1)

if __name__ == "__main__":
    main()
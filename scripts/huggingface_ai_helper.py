#!/usr/bin/env python3
"""
Hugging Face Inference API 辅助工具
用于风荷载计算项目的AI辅助功能
"""

import os
import requests
import json
import time
from typing import Dict, Any, Optional

class HuggingFaceAI:
    """Hugging Face AI API 封装类"""
    
    def __init__(self, api_token: str = None, model: str = None):
        """
        初始化Hugging Face AI
        
        参数:
            api_token: Hugging Face API Token
            model: 模型ID，默认 google/flan-t5-large
        """
        self.api_token = api_token or os.getenv("HF_TOKEN")
        self.model = model or os.getenv("HF_MODEL", "google/flan-t5-large")
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        
        if not self.api_token:
            raise ValueError("需要Hugging Face API Token。设置HF_TOKEN环境变量。")
    
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        查询Hugging Face API
        
        参数:
            prompt: 提示文本
            **kwargs: 额外参数
            
        返回:
            API响应结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # 默认参数
        params = {
            "inputs": prompt,
            "parameters": {
                "max_length": kwargs.get("max_length", 500),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "do_sample": kwargs.get("do_sample", True),
                "return_full_text": kwargs.get("return_full_text", False)
            },
            "options": {
                "wait_for_model": kwargs.get("wait_for_model", True),
                "use_cache": kwargs.get("use_cache", True)
            }
        }
        
        # 合并额外参数
        if "parameters" in kwargs:
            params["parameters"].update(kwargs["parameters"])
        
        try:
            response = requests.post(self.api_url, headers=headers, json=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return {"error": str(e)}
    
    def generate_documentation(self, code_content: str, doc_type: str = "function") -> str:
        """
        生成代码文档
        
        参数:
            code_content: 代码内容
            doc_type: 文档类型（function/class/module）
            
        返回:
            生成的文档
        """
        prompt = f"""请为以下{doc_type}代码生成中文文档说明：

代码：
```python
{code_content}
```

要求：
1. 简要说明功能
2. 列出参数说明
3. 说明返回值
4. 提供使用示例
5. 注意事项

请用Markdown格式回复。"""
        
        result = self.query(prompt, max_length=800)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "生成文档失败")
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return str(result)
    
    def explain_concept(self, concept: str, context: str = "风荷载计算") -> str:
        """
        解释技术概念
        
        参数:
            concept: 概念名称
            context: 上下文领域
            
        返回:
            概念解释
        """
        prompt = f"""请用中文解释{context}领域的'{concept}'概念：

要求：
1. 基本定义
2. 计算公式（如果有）
3. 工程应用
4. 相关规范
5. 实际示例

请用清晰易懂的语言，适合工程师理解。"""
        
        result = self.query(prompt, max_length=600)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "解释生成失败")
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return str(result)
    
    def generate_calculation_report(self, 
                                  building_params: Dict[str, Any],
                                  results: Dict[str, Any],
                                  code_standard: str = "GB50009") -> str:
        """
        生成风荷载计算报告
        
        参数:
            building_params: 建筑参数
            results: 计算结果
            code_standard: 使用规范
            
        返回:
            计算报告
        """
        prompt = f"""请生成一份专业的风荷载计算报告。

建筑参数：
{json.dumps(building_params, indent=2, ensure_ascii=False)}

计算结果：
{json.dumps(results, indent=2, ensure_ascii=False)}

使用规范：{code_standard}

报告要求：
1. 项目概述
2. 计算依据
3. 参数说明
4. 计算过程
5. 结果分析
6. 结论建议
7. 注意事项

请用专业的技术报告格式，包含必要的表格和数据。"""
        
        result = self.query(prompt, max_length=1000)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "报告生成失败")
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return str(result)
    
    def answer_technical_question(self, question: str, context: str = "") -> str:
        """
        回答技术问题
        
        参数:
            question: 技术问题
            context: 上下文信息
            
        返回:
            问题答案
        """
        if context:
            prompt = f"""基于以下上下文回答技术问题：

上下文：
{context}

问题：
{question}

要求：
1. 准确回答核心问题
2. 提供相关公式或规范引用
3. 给出实际应用建议
4. 如有不确定请说明"""
        else:
            prompt = f"""请回答以下风荷载计算相关技术问题：

问题：
{question}

要求：
1. 专业准确的回答
2. 引用相关规范
3. 提供计算思路
4. 工程应用建议"""
        
        result = self.query(prompt, max_length=800)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "回答生成失败")
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return str(result)

# 使用示例
def main():
    """使用示例"""
    # 从环境变量获取API Token
    hf_token = os.getenv("HF_TOKEN")
    
    if not hf_token:
        print("请设置HF_TOKEN环境变量")
        print("或在代码中直接提供API Token")
        return
    
    # 创建AI助手实例
    ai = HuggingFaceAI(api_token=hf_token)
    
    # 示例1：生成文档
    sample_code = """
def calculate_wind_pressure(height, terrain_category, location):
    \"\"\"
    计算风压
    \"\"\"
    # 计算逻辑
    pass
    """
    
    print("示例1：生成代码文档")
    docs = ai.generate_documentation(sample_code, "function")
    print(docs)
    print("-" * 50)
    
    # 示例2：解释概念
    print("示例2：解释技术概念")
    explanation = ai.explain_concept("基本风压", "建筑结构荷载")
    print(explanation)
    print("-" * 50)
    
    # 示例3：回答技术问题
    print("示例3：回答技术问题")
    answer = ai.answer_technical_question("GB50009中地面粗糙度类别如何确定？")
    print(answer)

if __name__ == "__main__":
    main()
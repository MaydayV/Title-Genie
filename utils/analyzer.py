import pandas as pd
from collections import Counter
import re

def analyze_performance(file) -> str:
    """
    Analyzes uploaded performance report (Excel) to find high-CTR keywords.
    
    Args:
        file: Uploaded Excel file with 'Product Name', 'Impressions', 'Clicks', 'CTR'.
        
    Returns:
        str: Summary of high-performing keywords to be used as context.
    """
    try:
        # Load data (assuming standard Alibaba export format or basic columns)
        # We need to handle potential format variations. 
        # For MVP, we look for 'Product Name' and 'CTR' or 'Clicks'/'Impressions'.
        
        df = pd.read_excel(file)
        
        # Normalize columns
        df.columns = [c.strip() for c in df.columns]
        
        # Check for required columns
        if 'Product Name' not in df.columns:
            return "Error: Performance file missing 'Product Name' column."
            
        # If CTR is missing, try to calculate it
        if 'CTR' not in df.columns:
            if 'Clicks' in df.columns and 'Impressions' in df.columns:
                df['CTR'] = df['Clicks'] / df['Impressions']
            else:
                return "Error: Could not calculate CTR. Missing 'CTR' or 'Clicks'/'Impressions' columns."
        
        # Ensure CTR is numeric (handle '1.5%' strings if any)
        if df['CTR'].dtype == object:
             df['CTR'] = df['CTR'].astype(str).str.rstrip('%').astype('float') / 100.0

        # Filter for High Performance (Top 25%)
        # Simple threshold: items with CTR > mean CTR
        threshold = df['CTR'].mean()
        high_performers = df[df['CTR'] > threshold]
        
        if high_performers.empty:
            return "未找到高 CTR 的产品 (CTR 高于平均值)。"
        
        # Extract Keywords from High Performers
        titles = high_performers['Product Name'].astype(str).tolist()
        all_text = " ".join(titles).lower()
        
        # Simple tokenization (cleaning non-alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text) # Ignore short words
        
        # Filter common stopwords (basic list)
        stopwords = set(['with', 'for', 'and', 'the', 'new', 'hot', 'sale', 'wholesale', 'china', 'high', 'quality'])
        filtered_words = [w for w in words if w not in stopwords]
        
        # Count frequency
        common_keywords = Counter(filtered_words).most_common(10)
        
        # Format output string
        result_lines = ["\n[历史效果分析]:"]
        result_lines.append(f"- 分析了 {len(df)} 个产品。发现了 {len(high_performers)} 个高表现产品 (CTR > {threshold:.2%})。")
        result_lines.append("- 根据历史数据提取的 '爆款' 关键词:")
        for word, count in common_keywords:
            result_lines.append(f"  * '{word.title()}' (在优秀标题中出现 {count} 次)")
            
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"分析失败: {str(e)}"

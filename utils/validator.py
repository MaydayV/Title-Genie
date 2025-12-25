import difflib
import pandas as pd
import re

def validate_brand(title, brand):
    """
    Ensures the Brand is present in the title. 
    If missing, prepends it. 
    If present but wrong case, we might leave it or fix it (fixing is safer).
    
    Returns:
        tuple: (corrected_title, was_fixed_bool)
    """
    if not brand or pd.isna(brand):
        return title, False
        
    brand_str = str(brand).strip()
    if not brand_str:
        return title, False

    # Case insensitive check
    if brand_str.lower() not in title.lower():
        # Force prepend
        return f"{brand_str} {title}", True
    
    return title, False

def check_duplication(new_title, existing_titles, threshold=0.8):
    """
    Checks if new_title is too similar to any in existing_titles.
    
    Returns:
        tuple: (is_duplicate_bool, similarity_score_float)
    """
    if not existing_titles:
        return False, 0.0
        
    max_score = 0.0
    for existing in existing_titles:
        score = difflib.SequenceMatcher(None, new_title.lower(), existing.lower()).ratio()
        if score > max_score:
            max_score = score
            
    return max_score > threshold, max_score

def calculate_seo_score(title, brand, main_kw, core_kw):
    """
    Calculates a 0-100 SEO Health Score.
    """
    score = 100
    reasons = []
    
    # 1. Length Check (Target: 80-120)
    # Penalize deviations
    length = len(title)
    if length < 80:
        penalty = (80 - length) * 1 # Lose 1 pt per char under
        score -= penalty
        reasons.append(f"太短 (-{penalty})")
    elif length > 120:
        penalty = (length - 120) * 2 # Lose 2 pts per char over (stricter)
        score -= penalty
        reasons.append(f"太长 (-{penalty})")
        
    # 2. Keyword Check
    # Brand
    if str(brand).lower() not in title.lower():
        score -= 20
        reasons.append("缺品牌 (-20)")
        
    # Core Keyword
    if str(core_kw).lower() not in title.lower():
        score -= 15
        reasons.append("缺核心词 (-15)")
        
    # 3. Formatting/Spam Check
    spam_words = ["new", "hot sale", "best", "cheap"]
    for word in spam_words:
        if re.search(r'\b' + re.escape(word) + r'\b', title, re.IGNORECASE):
            score -= 5
            reasons.append(f"含违禁词'{word}' (-5)")
            
    # 4. Starting Capital
    if title and title[0].islower():
        score -= 5
        reasons.append("首字母未大写 (-5)")
    
    # Floor score at 0
    return max(0, score), ", ".join(reasons)

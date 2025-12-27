import difflib
import pandas as pd
import re

def remove_punctuation(title):
    """
    Removes forbidden punctuation (commas, periods, exclamations, question marks).
    Keeps hyphens (-) and ampersands (&) as they are valid separators.
    """
    # Remove commas, periods, exclamation marks, question marks, semicolons, colons
    # Both English and Chinese punctuation
    title = re.sub(r'[,，。.!！?？;；:：]', ' ', title)
    # Collapse multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def check_punctuation(title):
    """
    Checks if forbidden punctuation exists in the title.
    Returns: (bool has_punctuation, list forbidden_chars_found)
    """
    # Find all occurrences of forbidden punctuation
    forbidden = re.findall(r'[,，。.!！?？;；:：]', title)
    return len(forbidden) > 0, list(set(forbidden))

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
        penalty = min(20, (80 - length) * 1) # Lose 1 pt per char under, max 20
        score -= penalty
        reasons.append(f"太短 (-{penalty})")
    elif length > 120:
        penalty = min(50, (length - 120) * 3) # Even stricter: 3 pts per char over, max 50
        score -= penalty
        reasons.append(f"太长({length}/120) (-{penalty})")
        
    # 2. Keyword Check
    def contains_kw(text, kw):
        if not kw or pd.isna(kw): return True
        # Normalize: remove non-alphanumeric for matching
        norm_text = re.sub(r'[^a-z0-9]', '', text.lower())
        norm_kw = re.sub(r'[^a-z0-9]', '', str(kw).lower())
        return norm_kw in norm_text

    # Brand
    if not contains_kw(title, brand):
        score -= 20
        reasons.append("缺品牌 (-20)")
        
    # Main Keyword
    if not contains_kw(title, main_kw):
        score -= 20
        reasons.append("缺主词 (-20)")
        
    # Core Keyword
    if not contains_kw(title, core_kw):
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

    # 5. Redundancy Check (Repeated phrases)
    words = re.findall(r'\b\w+\b', title.lower())
    
    # Extract all words from keywords to ignore them
    kw_text = f"{brand} {main_kw} {core_kw}".lower()
    kw_words = set(re.findall(r'\b\w+\b', kw_text))
    
    seen_words = set()
    repeated = []
    for w in words:
        if len(w) > 3 and w in seen_words and w not in kw_words:
            repeated.append(w)
        seen_words.add(w)
    
    if repeated:
        unique_repeated = list(set(repeated))
        penalty = len(unique_repeated) * 7
        score -= penalty
        reasons.append(f"含重复词 {unique_repeated} (-{penalty})")
    
    
    # 6. Punctuation Check (Strict No-Comma Policy)
    has_punct, punct_list = check_punctuation(title)
    if has_punct:
        score -= 10
        reasons.append(f"含禁止标点{punct_list} (-10)")

    # Floor score at 0
    return max(0, score), ", ".join(reasons)

def fix_acronyms(title):
    """
    Ensures common industry acronyms are always uppercase.
    """
    acronyms = [
        "POS", "LCD", "LED", "CPU", "RAM", "OS", "USB", "QR", "RFID", "VPC", 
        "NFC", "GPRS", "4G", "5G", "LTE", "SDK", "API", "OEM", "ODM", "IP", "IOS", "ANDROID"
    ]
    for ac in acronyms:
        # Match case-insensitively but replace with uppercase if it's a whole word
        pattern = re.compile(r'\b' + re.escape(ac) + r'\b', re.IGNORECASE)
        title = pattern.sub(ac, title)
    return title

def remove_filler_words(title):
    """
    Removes common starting filler words that waste character count.
    """
    fillers = ["The ", "A ", "An ", "the ", "a ", "an "]
    for f in fillers:
        if title.startswith(f):
            title = title[len(f):]
            break
    return title

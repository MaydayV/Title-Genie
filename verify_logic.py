import pandas as pd
import os
from dotenv import load_dotenv
from utils.prompt_builder import build_prompt
from utils.file_handler import load_file

load_dotenv()

def verify_logic():
    print("--- 1. Creating Mock CSV ---")
    data = {
        "Brand": ["TechNova", "EcoLife"],
        "Main Keyword": ["Wireless Earbuds", "Bamboo Toothbrush"],
        "Core Keyword": ["Bluetooth 5.0 Headphones", "Biodegradable Soft Bristles"],
        "Selling Points": ["Noise Cancelling, 24h Battery", "Pack of 4, BPA Free"],
        "Attributes": ["Black, Waterproof", "Natural Wood Handle"],
        "Other Col": ["Ignore Me", "Ignore Me"]
    }
    df_mock = pd.DataFrame(data)
    df_mock.to_csv("test_data.csv", index=False)
    
    print("--- 2. Loading CSV Data ---")
    try:
        with open("test_data.csv", "rb") as f:
            # We need a file-like object with a 'name' attribute for our handler
            # In streamlit it's an UploadedFile, here we mock it somewhat or just pass a file object?
            # Our handler checks file.name. Let's subclass or mock.
            class MockFile(io.BytesIO):
                def __init__(self, content, name):
                    super().__init__(content)
                    self.name = name
            
            f.seek(0)
            mock_file = MockFile(f.read(), "test_data.csv")
            
            df = load_file(mock_file)
            print(f"Loaded {len(df)} rows from CSV.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("\n--- 3. Testing Prompt Builder (New Constraints) ---")
    row = df.iloc[0]
    prompt = build_prompt(row, mode="Mode A")
    print(f"Prompt (Mode A):\n{prompt}") 
    
    if "80 - 120 characters" in prompt:
        print("\n[SUCCESS] Length constraint found in prompt.")
    else:
        print("\n[FAILURE] Length constraint NOT found.")
        
    if "SEO Front-Loading" in prompt:
        print("[SUCCESS] SEO Front-Loading constraint found.")
    else:
        print("[FAILURE] SEO Front-Loading constraint MISSING.")
        
    if "ACRONYMS" in prompt:
        print("[SUCCESS] Acronym rule found.")
    else:
         print("[FAILURE] Acronym rule MISSING.")
         
    if "NO Redundancy" in prompt:
         print("[SUCCESS] Redundancy rule found.")
    else:
         print("[FAILURE] Redundancy rule MISSING.")

    if "Attributes: Black, Waterproof" in prompt: # Dynamic context check
         print("[SUCCESS] Dynamic attributes found in Context.")
         
    print("\n--- 4. Testing Mode B (Few-Shot) ---")
    prompt_b = build_prompt(row, mode="Mode B")
    if "Examples of Good Titles" in prompt_b:
        print("[SUCCESS] Few-Shot examples found in Mode B.")
    else:
        print("[FAILURE] Few-Shot examples missing in Mode B.")

    print("\n--- 5. Testing Phase 2: Performance Analysis ---")
    from utils.analyzer import analyze_performance
    
    # We need to simulate the file load again or just pass the path if analyzer supports it?
    # Our analyzer expects a file-like object or path compatible with pd.read_excel
    try:
        # Generate the mock file first if needed, assuming it exists from previous step
        analysis_result = analyze_performance("mock_performance.xlsx")
        print("Analysis Result Preview:")
        print(analysis_result[:200] + "...")
        
        if "Winning Keywords" in analysis_result or "Identifying winning keywords" in analysis_result:
             print("[SUCCESS] Analyzer returned keywords.")
        else:
             print("[FAILURE] Analyzer failed to identify keywords.")
             
        # Test Prompt Integration
        prompt_with_context = build_prompt(row, mode="Mode B", extra_context=analysis_result)
        if "HISTORICAL PERFORMANCE INSIGHTS" in prompt_with_context:
            print("[SUCCESS] Performance context injected into Prompt.")
        else:
            print("[FAILURE] Performance context MISSING from Prompt.")
            
    except Exception as e:
        print(f"Phase 2 Test Failed: {e}")

    import re
    print("\n--- 6. Testing Output Processing (Row Explosion) ---")
    mock_ai_output = """1. Title One
2. Title Two
3. Title Three"""
    
    lines = mock_ai_output.split('\n')
    titles = []
    for line in lines:
        clean = re.sub(r'^\d+\.?\s*', '', line.strip())
        if clean: titles.append(clean)
        
    if len(titles) == 3 and titles[0] == "Title One":
        print("[SUCCESS] Title parsing logic works correctly.")
    else:
        print(f"[FAILURE] Title parsing failed: {titles}")

    print("\n--- 7. Testing Validators (Phase 3) ---")
    from utils.validator import validate_brand, check_duplication, calculate_seo_score
    
    # Brand Check
    title_no_brand = "Wireless Earbuds Blue"
    fixed_title, fixed = validate_brand(title_no_brand, "TechNova")
    if fixed and "TechNova" in fixed_title:
        print(f"[SUCCESS] Brand fixed: {fixed_title}")
    else:
        print(f"[FAILURE] Brand fix failed: {fixed_title}")
        
    # Dedup
    existing = ["TechNova Wireless Earbuds", "Some Other Title"]
    dup_title = "TechNova Wireless Earbuds" # Exact match
    is_dup, score = check_duplication(dup_title, existing)
    if is_dup:
        print(f"[SUCCESS] Duplicate detected (Score: {score:.2f})")
    else:
        print(f"[FAILURE] Duplicate NOT detected (Score: {score:.2f})")
        
    # SEO Score
    # Good Title
    good_title = "TechNova Wireless Earbuds Bluetooth 5.0 Headphones with Noise Cancelling for Gym" # ~80 chars
    score_val, notes = calculate_seo_score(good_title, "TechNova", "Wireless Earbuds", "Headphones")
    print(f"Good Title Score: {score_val} ({notes})")
    if score_val > 90:
        print("[SUCCESS] Good title scored high.")
    else:
        print("[FAILURE] Good title scored low.")

import io
if __name__ == "__main__":
    verify_logic()

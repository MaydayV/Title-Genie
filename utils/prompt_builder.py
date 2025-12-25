import pandas as pd

def build_prompt(row, mode="Mode A", extra_context=""):
    """
    Constructs the prompt for Qwen based on the product data row and selected mode.
    """
    
    # Mandatory Keys
    brand = row.get('Brand', '')
    main_kw = row.get('Main Keyword', '')
    core_kw = row.get('Core Keyword', '')
    
    # Context
    context_items = []
    
    if extra_context:
        context_items.append(f"--- HISTORICAL PERFORMANCE INSIGHTS ---\n{extra_context}\n---------------------------------------")
        
    for key, val in row.items():
        if key not in ['Brand', 'Main Keyword', 'Core Keyword', 'Generated Titles', 'Original Row ID'] and pd.notna(val) and str(val).strip() != '':
            context_items.append(f"- {key}: {val}")
    context_str = "\n".join(context_items)
    
    # FEW-SHOT EXAMPLES (Mode B Focus)
    few_shot_examples = """
Examples of Good Titles (Natural & High CTR):
1. TechNova Wireless Earbuds - Bluetooth 5.0 Headphones with Noise Cancelling & 24h Battery for Gym
2. EcoLife Bamboo Toothbrush Pack of 4 - Biodegradable Soft Bristles for Sensitive Gums, Plastic-Free
3. PRO-X Gaming Mouse - High Precision Optical Sensor RGB Wired Mouse for Esports, 16000 DPI

Examples of BAD Titles (Do NOT do this):
1. TechNova Wireless Earbuds Bluetooth 5.0 Headphones Noise Cancelling 24h Battery Gym (Just keywords piled up)
2. Wireless Earbuds by TechNova with Bluetooth 5.0 Headphones (Repetitive, boring structure)
"""

    role_instruction = "Role: You are an Alibaba International Station SEO expert. Your goal is to write high-converting product titles."

    constraints = """
CRITICAL CONSTRAINTS (Must Follow):
1. **Length**: 80 - 120 characters limits.
2. **Keywords**: strictly include "{brand}", "{main_kw}", and "{core_kw}".
3. **SEO Front-Loading**: Place the most important keywords ({brand} + {core_kw}) within the **first 60 characters**.
4. **Format**: 
    - Capitalize First Letters (Title Case). 
    - **ACRONYMS**: Always uppercase standard acronyms (e.g., POS, LED, LCD, CPU). Do NOT write 'Pos' or 'Led'.
5. **Readability**: 
    - **NO Redundancy**: If "{main_kw}" and "{core_kw}" imply the same thing (e.g. "Desktop POS" and "POS Solutions"), merge them naturally. Do NOT say "Desktop POS POS Solutions".
    - **Fluidity**: Make it read like a sentence, not a robot list. Use prepositions.
    - **Separators**: Use `-` or `|` sparingly (max 1-2 times).
6. **Logic**: Do NOT just concatenate. Make it readable.
""".format(brand=brand, main_kw=main_kw, core_kw=core_kw)

    if mode == "Mode A": # Strict
        strategy = f"""
Strategy: STRICT STRUCTURE
Structure: [Brand] + [Key Specs/Attributes] + [Core Keyword] + [Main Keyword Integration]
Context:
{context_str}

Task: Generate title strictly following the structure above.
"""
    else: # Mode B: Natural - UPDATED
        strategy = f"""
Strategy: NATURAL & COMMERCIAL
Target Audience: Native English speakers (US/EU).
Goal: Maximize Click-Through Rate (CTR).
Context:
{context_str}

{few_shot_examples}

Instruction:
1. Analyze the 'Context' to find the most attractive selling points (e.g. material, application, certifications).
2. Combine "{brand}", "{main_kw}", and "{core_kw}" with those selling points into a fluid, grammatically correct sentence.
3. Use benefits to persuade the buyer (e.g. "for Retail", "High efficiency").
"""

    return f"{role_instruction}\n{constraints}\n{strategy}"

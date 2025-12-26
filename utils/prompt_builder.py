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

    role_instruction = "Role: You are an Alibaba International Station SEO expert specializing in high-converting product titles for global markets."

    constraints = """
CRITICAL CONSTRAINTS (Strict Compliance Required):
1. **Length**: 80 - 120 characters limits. **THIS IS A HARD LIMIT. IF THE TITLE EXCEEDS 120 CHARACTERS, IT WILL FAIL. PRUNE SPECIFICATIONS IF NECESSARY.**
2. **Mandatory Keywords**: strictly include "{brand}", "{main_kw}", and "{core_kw}".
3. **SEO Front-Loading**: The title MUST start with "{brand} {main_kw}". This is non-negotiable for brand recognition and SEO.
4. **Format**: 
    - Capitalize First Letters (Title Case). 
    - **ACRONYMS**: Always uppercase standard acronyms (e.g., POS, LED, LCD, CPU, RAM, OS).
5. **Readability**: 
    - **NO Redundancy**: Do not repeat the same keyword phrase twice unless used in a different context.
    - **Fluidity**: Use natural English flow. Incorporate market-specific adjectives and synonyms to extend the title naturally.
    - **Separators**: Use `-` or `|` only to separate distinct thought blocks.
""".format(brand=brand, main_kw=main_kw, core_kw=core_kw)

    if mode == "Mode A": # Strict
        strategy = f"""
Strategy: STRICT STRUCTURE
Structure: [Brand] + [Main Keyword] + [Key Specs/Attributes] + [Core Keyword]
Context:
{context_str}

Task: Generate title strictly following the structure above.
"""
    else: # Mode B: Natural & Commercial
        strategy = f"""
Strategy: COMMERCIAL & CONVERSATIONAL
Target Audience: Global B2B buyers seeking professional product solutions.
Context (Use these variables to enrich the title):
{context_str}

{few_shot_examples}

Instruction:
1. Start exactly with "{brand} {main_kw}".
2. Integrate "{core_kw}" and other key attributes (like product model, CPU, OS, etc. from context) naturally.
3. **DIVERSITY**: When generating multiple titles, ensure each title focuses on a DIFFERENT aspect:
    - Title 1: Focus on Technical Specs & Performance.
    - Title 2: Focus on Application Scenarios (e.g., Retail, Kitchen, Warehouse).
    - Title 3: Focus on User Benefits (e.g., Productivity, Error-reduction, Durability).
    - Title 4: Focus on Design & Material.
    - Title 5: Focus on Market Keywords & Commercial Appeal.
4. Use commercial synonyms (e.g., "Advanced", "Smart", "Efficient", "Industrial-grade") to improve appeal.
5. Ensure the total length is between 80-120 characters.
6. Make it sound like a premium product listing, not a keyword list.
"""

    return f"{role_instruction}\n{constraints}\n{strategy}"

    return f"{role_instruction}\n{constraints}\n{strategy}"

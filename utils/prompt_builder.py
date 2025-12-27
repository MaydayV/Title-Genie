import pandas as pd

def build_prompt(row, mode="Mode A", extra_context="", keyword_positions=None, starred_fields=None):
    """
    Constructs the prompt for Qwen based on the product data row and selected mode.
    keyword_positions: dict like {'Brand': '前', 'Main Keyword': '中', ...}
    starred_fields: list of field names that MUST be included.
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
    
    # Keyword Positioning Rules
    pos_rules = []
    if keyword_positions:
        # Map generic names to actual values for clarity in prompt
        # We use the terms "Brand", "Main Keyword", "Core Keyword" as placeholders in instruction
        
        for kw_type, pos in keyword_positions.items():
            kw_val = row.get(kw_type, '')
            if not kw_val: continue
            
            if pos == "前 (Front)":
                pos_rules.append(f"- The {kw_type} '{kw_val}' MUST appear at the VERY BEGINNING (first 30 characters).")
            elif pos == "中 (Middle)":
                pos_rules.append(f"- The {kw_type} '{kw_val}' should appear in the MIDDLE section of the title.")
            elif pos == "尾 (End)":
                pos_rules.append(f"- The {kw_type} '{kw_val}' MUST appear at the VERY END of the title.")
                
    positioning_instruction = "\n".join(pos_rules) if pos_rules else ""

    # Starred Fields Logic
    starred_instruction = ""
    if starred_fields:
        starred_items = []
        for field in starred_fields:
            value = row.get(field, '')
            if value and pd.notna(value):
                starred_items.append(f'"{field}": "{value}"')
        if starred_items:
            starred_instruction = f"""
**STARRED FIELDS (MUST INCLUDE - can be AI-optimized/extracted):**
{chr(10).join(starred_items)}
The content of these fields MUST be included in the generated titles. You may rephrase, extract key identifiers, or optimize the wording to fit better, but the CORE INFORMATION from these fields must be present.
"""

    # FEW-SHOT EXAMPLES (Mode B Focus)
    few_shot_examples = """
Examples of Good Titles (Natural & High CTR):
1. TechNova Wireless Earbuds - Bluetooth 5.0 Headphones with Noise Cancelling & 24h Battery for Gym
2. EcoLife Bamboo Toothbrush Pack of 4 - Biodegradable Soft Bristles for Sensitive Gums, Plastic-Free
3. PRO-X Gaming Mouse - High Precision Optical Sensor RGB Wired Mouse for Esports, 16000 DPI

Examples of BAD Titles (Do NOT do this):
1. TechNova Wireless Earbuds, Bluetooth 5.0 Headphones, Noise Cancelling, 24h Battery Gym (Uses commas - FORBIDDEN)
2. Wireless Earbuds by TechNova with Bluetooth 5.0 Headphones (Repetitive structure)
3. TechNova Wireless Earbuds Bluetooth 5.0 Headphones Noise Cancelling (Just keywords piled up)
"""

    role_instruction = "Role: You are an Alibaba International Station SEO expert specializing in high-converting product titles for global markets."

    constraints = f"""
CRITICAL CONSTRAINTS (Strict Compliance Required):

1. **Length**: 80 - 120 characters limits. **THIS IS A HARD LIMIT. IF THE TITLE EXCEEDS 120 CHARACTERS, IT WILL FAIL. PRUNE SPECIFICATIONS IF NECESSARY.**

2. **Mandatory Keywords**: strictly include "{brand}", "{main_kw}", and "{core_kw}".

3. **Keyword Positioning**:
{positioning_instruction}

4. **NO PUNCTUATION**:
   - **ABSOLUTELY NO COMMAS (,) or PERIODS (.) or EXCLAMATION MARKS (!)**.
   - Use ONLY hyphens (-) to separate distinct thought blocks.
   - Use spaces to separate words.
   - Example: "{brand} {main_kw} - {core_kw} with High Performance"

5. **Format**: 
    - Capitalize First Letters (Title Case). 
    - **ACRONYMS**: Always uppercase standard acronyms (e.g., POS, LED, LCD, CPU, RAM, OS).

6. **Readability & Quality**: 
    - **NO Redundancy**: Do not repeat the same keyword phrase twice.
    - **Fluidity**: Use natural English flow. 
    - **NO Spam Words**: Avoid "New", "Hot Sale", "Best", "Cheap".
    
{starred_instruction}
"""

    if mode == "Mode A": # Strict
        strategy = f"""
Strategy: STRICT STRUCTURE
Structure: [Brand] + [Main Keyword] + [Key Specs/Attributes] + [Core Keyword]
(Adjust structure ONLY IF Positioning Rules above require it)

Context:
{context_str}

Task: Generate title strictly following the structure and constraints.
"""
    else: # Mode B: Natural & Commercial
        strategy = f"""
Strategy: COMMERCIAL & CONVERSATIONAL
Target Audience: Global B2B buyers seeking professional product solutions.
Context (Use these variables to enrich the title):
{context_str}

{few_shot_examples}

Instruction:
1. Start exactly according to the positioning rules (default to "{brand} {main_kw}" if no rules).
2. Integrate "{core_kw}" and other key attributes naturally.
3. **DIVERSITY**: When generating multiple titles, ensure each title focuses on a DIFFERENT aspect (Tech Specs, Usage, Benefits).
4. Use commercial adjectives (e.g., "Advanced", "Smart", "Efficient") but NO SPAM WORDS.
5. Ensure the total length is between 80-120 characters.
"""

    return f"{role_instruction}\n{constraints}\n{strategy}"

    return f"{role_instruction}\n{constraints}\n{strategy}"

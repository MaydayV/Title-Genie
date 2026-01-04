import streamlit as st
import pandas as pd
import os
import re
import json
import time
from utils.file_handler import load_file, export_excel
from utils.prompt_builder import build_prompt
from utils.text_gen import generate_text
from utils.validator import (
    validate_brand, 
    check_duplication, 
    calculate_seo_score, 
    fix_acronyms, 
    remove_filler_words,
    remove_punctuation
)
from utils.title_history import TitleHistoryManager

# Load environment variables (Local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Initialize browser localStorage (Optional)
class MockLocalStorage:
    def getItem(self, key): return None
    def setItem(self, key, value): pass

try:
    from streamlit_local_storage import LocalStorage
    localStorage = LocalStorage()
except ImportError:
    localStorage = MockLocalStorage()

# --- Helper Functions for Config Persistence (Browser LocalStorage) ---
LOCAL_STORAGE_KEY = "title_genie_config"

def load_config_from_browser():
    """Load config from browser localStorage"""
    try:
        data = localStorage.getItem(LOCAL_STORAGE_KEY)
        if data:
            return json.loads(data) if isinstance(data, str) else data
    except Exception:
        pass
    return {}

def save_config_to_browser(config):
    """Save config to browser localStorage"""
    try:
        localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(config))
    except Exception:
        pass

st.set_page_config(page_title="Title Genie 标题精灵", page_icon="🧞", layout="wide")

def main():
    st.title("🧞 Title Genie 标题精灵 (Beta)")
    st.markdown("阿里国际站标题自动化生成工具")

    # Load config from browser localStorage
    # local_config = load_config_from_browser() # This line is moved inside main() and show_settings_dialog()

    # Initialize History Manager with browser localStorage
    # history_manager = TitleHistoryManager(local_storage=localStorage) # This line is moved inside main()

@st.dialog("⚙️ 设置 (Configuration)", width="large")
def show_settings_dialog(history_manager):
    # API Key Management
    local_config = load_config_from_browser()
    
    st.subheader("🔑 API 设置")
    api_key_input = st.text_input(
        "DashScope API Key (通义千问)", 
        value=st.session_state.get('api_key', ''),
        type="password",
        help="请从阿里云 DashScope 控制台获取 API Key",
        key="api_key_dialog"
    )
    
    # Update session state & auto-save to browser localStorage on change
    if api_key_input != st.session_state.get('api_key'):
        st.session_state['api_key'] = api_key_input
        local_config["api_key"] = api_key_input
        save_config_to_browser(local_config)
        st.toast("API Key 已保存", icon="💾")

    # Model Selection
    model_name = st.selectbox(
        "选择模型 (Model)",
        options=["qwen-flash", "qwen-plus", "qwen-turbo", "qwen-max"],
        index=["qwen-flash", "qwen-plus", "qwen-turbo", "qwen-max"].index(st.session_state.get('model_name', 'qwen-flash')),
        help="推荐使用 qwen-flash 以获得最快的生成速度。",
        key="model_dialog"
    )
    st.session_state['model_name'] = model_name

    # Keyword Positioning
    st.divider()
    st.subheader("📍 关键词位置设置")
    pos_options = ["前 (Front)", "中 (Middle)", "尾 (End)"]
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.session_state['pos_brand'] = st.selectbox("品牌词", pos_options, 
                                                    index=pos_options.index(st.session_state.get('pos_brand', "前 (Front)")), 
                                                    key="brand_pos_dialog")
    with col_p2:
        st.session_state['pos_main'] = st.selectbox("主词", pos_options, 
                                                   index=pos_options.index(st.session_state.get('pos_main', "前 (Front)")), 
                                                   key="main_pos_dialog")
    with col_p3:
        st.session_state['pos_core'] = st.selectbox("核心词", pos_options, 
                                                   index=pos_options.index(st.session_state.get('pos_core', "尾 (End)")), 
                                                   key="core_pos_dialog")

    # Strategy Selection
    st.divider()
    st.subheader("🤖 生成策略设置")
    mode_index = 1 if st.session_state.get('selected_mode_label', "Mode B (营销模式)") == "Mode B (营销模式)" else 0
    mode = st.radio(
        "选择生成模式",
        ("Mode A (严格模式)", "Mode B (营销模式)"),
        index=mode_index,
        help="选择 'Mode A' 进行严格格式化，或选择 'Mode B' 以获得更好的点击率。",
        key="mode_dialog"
    )
    st.session_state['selected_mode_label'] = mode
    
    # Generation Count
    num_titles = st.slider("每个产品生成标题数量", 1, 10, st.session_state.get('num_titles', 5), key="num_titles_dialog")
    st.session_state['num_titles'] = num_titles

    # History Management
    st.divider()
    st.subheader("🔍 历史库管理")
    stats = history_manager.get_stats()
    st.caption(f"当前历史库已有标题: {stats['total_titles']} 条")
    if st.button("清除历史库 (Clear History)", type="secondary", key="clear_history_dialog"):
            history_manager.clear_history()
            history_manager.save_history()
            st.toast("历史库已清空")
            st.rerun()

def main():
    # Header with Settings button
    col_title, col_settings = st.columns([8, 1])
    with col_title:
        st.title("🧞 Title Genie 标题精灵 (Beta)")
        st.markdown("阿里国际站标题自动化生成工具")
    with col_settings:
        st.write("") # Padding
        if st.button("⚙️ 设置", use_container_width=True):
            show_settings_dialog(history_manager)

    # Initialize session state defaults if not present
    if 'model_name' not in st.session_state: st.session_state['model_name'] = "qwen-flash"
    if 'pos_brand' not in st.session_state: st.session_state['pos_brand'] = "前 (Front)"
    if 'pos_main' not in st.session_state: st.session_state['pos_main'] = "前 (Front)"
    if 'pos_core' not in st.session_state: st.session_state['pos_core'] = "尾 (End)"
    if 'selected_mode_label' not in st.session_state: st.session_state['selected_mode_label'] = "Mode B (营销模式)"
    if 'num_titles' not in st.session_state: st.session_state['num_titles'] = 5

    # Load config from browser localStorage for initial API key
    local_config = load_config_from_browser()

    # Initialize History Manager with browser localStorage
    history_manager = TitleHistoryManager(local_storage=localStorage)

    # API Key Initial Sync
    if 'api_key' not in st.session_state:
        env_key = ""
        try:
            env_key = st.secrets.get("DASHSCOPE_API_KEY", "")
        except Exception: pass
        if not env_key:
            env_key = os.getenv("DASHSCOPE_API_KEY", "")
        st.session_state['api_key'] = env_key if env_key else local_config.get("api_key", "")

    # Derived values for logic
    keyword_positions = {
        "Brand": st.session_state['pos_brand'],
        "Main Keyword": st.session_state['pos_main'],
        "Core Keyword": st.session_state['pos_core']
    }
    selected_mode = "Mode A" if "Mode A" in st.session_state['selected_mode_label'] else "Mode B"
    num_titles = st.session_state['num_titles']
    api_key_input = st.session_state['api_key']
    model_name = st.session_state['model_name']

    # --- Main Content ---
    
    # 1. Product Data Upload
    uploaded_file = st.file_uploader("上传产品资料表 (支持 Excel 或 CSV)", type=["xlsx", "csv"], key="main_file")
    
    st.divider()

    # 2. Performance Data (Optional)
    performance_context = ""
    with st.expander("📈 智能数据分析 (可选)", expanded=False):
        st.write("上传阿里后台的“商品分析”报表 (Excel)，AI 将自动分析高点击词并在生成新标题时参考。")
        perf_file = st.file_uploader("上传效果报表", type=["xlsx"], key="perf")
        
        if perf_file:
            from utils.analyzer import analyze_performance
            with st.spinner("正在分析历史表现数据..."):
                performance_context = analyze_performance(perf_file)
                st.info(performance_context)
    
    if uploaded_file:
        try:
            df = load_file(uploaded_file)
            st.success(f"文件上传成功！共加载 {len(df)} 行数据。")
            
            with st.expander("数据预览", expanded=True):
                st.dataframe(df.head())
            
            # Column Validation
            df.columns = df.columns.str.strip()
            required_columns = ['Brand', 'Main Keyword', 'Core Keyword']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                st.error(f"缺少必要列: {', '.join(missing_cols)}")
                return

            # --- Resume / Checkpoint Logic ---
            if 'processed_indices' not in st.session_state:
                st.session_state['processed_indices'] = set()
                st.session_state['results_list'] = []

            processed_count = len(st.session_state['processed_indices'])
            total_rows = len(df)
            
            # --- Starred Fields Selection ---
            st.divider()
            st.subheader("⭐ 星标字段设置")
            st.caption("选择最多2个字段，其内容将强制包含在标题中（可AI优化）。")
            
            # Exclude mandatory keywords from selection
            exclude_keywords = ['Brand', 'Main Keyword', 'Core Keyword', 'Generated Titles', 'Original Row ID']
            available_star_cols = [c for c in df.columns if c not in exclude_keywords and c.strip() != '']
            
            starred_fields = st.multiselect(
                "选择星标字段 (最多2个)",
                options=available_star_cols,
                max_selections=2,
                key="starred_fields_select",
                help="所选字段的内容会被加入提示词，要求AI必须体现在标题中。"
            )

            
            # --- Generation Trigger ---
            btn_label = "开始生成标题" if processed_count == 0 else f"继续生成 (已完成 {processed_count}/{total_rows})"
            
            if st.button(btn_label, type="primary"):
                if not api_key_input:
                    st.error("请提供 API Key。")
                    return
                
                progress_bar = st.progress(processed_count / total_rows)
                status_text = st.empty()
                time_estimator = st.empty()
                
                start_time = time.time()
                
                # Iterate
                for index, row in df.iterrows():
                    if index in st.session_state['processed_indices']:
                        continue # Skip already processed
                    
                    # Estimate remaining time
                    processed_in_session = len(st.session_state['processed_indices']) - processed_count + 1 # simplistic
                    elapsed = time.time() - start_time
                    if processed_in_session > 1:
                        avg_time = elapsed / (processed_in_session - 1)
                        remaining = (total_rows - len(st.session_state['processed_indices'])) * avg_time
                        time_estimator.caption(f"预计剩余时间: {int(remaining // 60)}分 {int(remaining % 60)}秒")

                    main_kw_display = row.get('Main Keyword', '未知产品')
                    if pd.isna(main_kw_display): main_kw_display = '未知产品'
                    
                    status_text.markdown(f"**正在处理 ({index + 1}/{total_rows})**: `{main_kw_display}`")
                    
                    # Build Prompt
                    role_instruction = "Role: You are an Alibaba International Station SEO expert specializing in high-converting product titles for global markets."
                    prompt = build_prompt(
                        row, 
                        selected_mode, 
                        extra_context=performance_context,
                        keyword_positions=keyword_positions,
                        starred_fields=starred_fields
                    )
                    full_prompt = f"{prompt}\n\nTask: Generate {num_titles} distinct, professional titles for this product. Output them as a numbered list (1. Title...)."
                    
                    # Call API
                    generated_content = generate_text(full_prompt, api_key_input, model_name)
                    
                    # Parse Content
                    lines = generated_content.split('\n')
                    generated_titles_for_this_row = [] 
                    
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        
                        clean_title = re.sub(r'^\d+\.?\s*', '', line)
                        if len(clean_title) < 10: continue

                        # 0. Post-AI Cleanup & Normalization
                        clean_title = remove_punctuation(clean_title)  # Remove commas/periods FIRST
                        clean_title = remove_filler_words(clean_title)
                        clean_title = fix_acronyms(clean_title)

                        # 1. Brand Validation
                        clean_title, fixed = validate_brand(clean_title, row.get('Brand', ''))
                        
                        # 2. Duplicate Detection (Batch + History)
                        # Check batch dupes
                        is_dup_batch, _ = check_duplication(clean_title, generated_titles_for_this_row)
                        if is_dup_batch: continue
                        
                        # Check history dupes (Cross-Library)
                        is_dup_hist, score_hist, sim_title = history_manager.check_similarity(clean_title, threshold=0.8)
                        
                        # Note: We might still want to show it but flag it? Or filter it?
                        # For now, let's filter if it's a strong match > 0.9, otherwise just warn in notes
                        dup_note = ""
                        if is_dup_hist:
                             if score_hist > 0.95:
                                 continue # Skip identicals
                             dup_note = f" (与历史标题相似度 {score_hist:.0%})"

                        generated_titles_for_this_row.append(clean_title)

                        # 3. SEO Scoring
                        seo_score, seo_notes = calculate_seo_score(
                            clean_title, 
                            row.get('Brand', ''), 
                            row.get('Main Keyword', ''), 
                            row.get('Core Keyword', '')
                        )
                        
                        # --- AI Polishing Loop (Self-Correction) ---
                        attempts = 0
                        max_attempts = 2
                        while seo_score < 100 and attempts < max_attempts:
                            attempts += 1
                            polish_prompt = f"""
{role_instruction}
The following title needs optimization to reach a perfect SEO score (100).
Current Title: "{clean_title}"
Current Character Count: {len(clean_title)}
REQUIRED Character Count: 80 - 120 (STRICT HARD LIMIT: DO NOT EXCEED 120)
Faults Identified: {seo_notes}
Mandatory Keywords: "{row.get('Brand', '')}", "{row.get('Main Keyword', '')}", "{row.get('Core Keyword', '')}"

Task: Rewrite the title to fix all faults. 
If it's too long, you MUST REMOVE non-essential descriptive words or specifications.
The new title MUST:
1. Start with "{row.get('Brand', '')} {row.get('Main Keyword', '')}"
2. Include "{row.get('Core Keyword', '')}"
3. Be between 80 - 120 characters total.
Output ONLY the new title.
"""
                            polished_title = generate_text(polish_prompt, api_key_input, model_name).strip()
                            polished_title = re.sub(r'^["\']|["\']$', '', polished_title) # Remove quotes
                            
                            # Re-Validate
                            new_score, new_notes = calculate_seo_score(
                                polished_title, 
                                row.get('Brand', ''), 
                                row.get('Main Keyword', ''), 
                                row.get('Core Keyword', '')
                            )
                            
                            if new_score >= seo_score:
                                clean_title = polished_title
                                seo_score = new_score
                                seo_notes = f"[Polished V{attempts}] {new_notes}"
                                if seo_score == 100:
                                    break

                        result_row = {
                            "原行号 (Row ID)": index + 1,
                            "品牌 (Brand)": row.get('Brand', ''),
                            "主词 (Main Keyword)": row.get('Main Keyword', ''),
                            "核心词 (Core Keyword)": row.get('Core Keyword', ''),
                            "AI 生成标题 (AI Suggestions)": clean_title,
                            "SEO 得分": seo_score,
                            "扣分原因": seo_notes + dup_note
                        }
                        st.session_state['results_list'].append(result_row)
                        
                        # ** Add to History Immediately **
                        history_manager.add_title(clean_title, brand=row.get('Brand', ''), product_id=f"Row-{index+1}")

                    # Mark as processed
                    st.session_state['processed_indices'].add(index)
                    progress_bar.progress(len(st.session_state['processed_indices']) / total_rows)
                    
                    # Auto-save history every row (safer)
                    history_manager.save_history()
                
                status_text.success("生成完成！")
                time_estimator.empty()
                
        except Exception as e:
            st.error(f"发生错误: {e}")
            st.exception(e)

    # --- Results & Export ---
    if 'results_list' in st.session_state and st.session_state['results_list']:
        st.divider()
        st.subheader("生成结果")
        
        # Convert list to DF for logic
        results_df = pd.DataFrame(st.session_state['results_list'])
        
        edited_df = st.data_editor(
            results_df,
            num_rows="dynamic",
            use_container_width=True,
            height=400
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
             # Download
            st.download_button(
                label="📥 下载结果 (Excel)",
                data=export_excel(edited_df),
                file_name="title_genie_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            if st.button("🗑️ 清空当前任务结果", help="清除页面缓存和进度，开始新任务"):
                st.session_state['results_list'] = []
                st.session_state['processed_indices'] = set()
                st.rerun()

if __name__ == "__main__":
    main()

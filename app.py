import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from utils.file_handler import load_file, export_excel
from utils.prompt_builder import build_prompt
from utils.text_gen import generate_text
from utils.validator import validate_brand, check_duplication, calculate_seo_score

# Load environment variables
load_dotenv()

# --- Helper Functions for Config Persistence ---
CONFIG_FILE = ".title_genie_config.json"
import json
import time
from utils.title_history import TitleHistoryManager

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except:
        pass

st.set_page_config(page_title="Title Genie 标题精灵", page_icon="🧞", layout="wide")

def main():
    st.title("🧞 Title Genie 标题精灵 (Beta)")
    st.markdown("阿里国际站标题自动化生成工具")

    # Load local config
    local_config = load_config()

    # Initialize History Manager
    history_manager = TitleHistoryManager()

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("设置 (Configuration)")
        
        # API Key Management
        if 'api_key' not in st.session_state:
            # Try env var first, then local config
            env_key = os.getenv("DASHSCOPE_API_KEY", "")
            st.session_state['api_key'] = env_key if env_key else local_config.get("api_key", "")
            
        api_key_input = st.text_input(
            "DashScope API Key (通义千问)", 
            value=st.session_state['api_key'],
            type="password",
            help="请从阿里云 DashScope 控制台获取 API Key",
            key="api_key_input"
        )
        # Update session state & auto-save to local config on change
        if api_key_input != st.session_state['api_key']:
            st.session_state['api_key'] = api_key_input
            local_config["api_key"] = api_key_input
            save_config(local_config)
            st.toast("API Key 已保存", icon="💾")
        
        # Model Selection
        st.subheader("模型设置")
        model_name = st.selectbox(
            "选择模型 (Model)",
            options=["qwen-flash", "qwen-plus", "qwen-turbo", "qwen-max"],
            index=0, # Default to qwen-flash
            help="推荐使用 qwen-flash 以获得最快的生成速度。"
        )

        # Strategy Selection
        st.subheader("生成策略设置")
        with st.expander("ℹ️ 策略说明指南"):
            st.markdown("""
            **模式 A (严格合规模式):**
            - **适用场景:** 标准化产品目录，对格式要求严格。
            - **逻辑:** 严格遵循 `品牌 + 规格/属性 + 核心词` 的排序结构。
            
            **模式 B (高点击/营销模式):**
            - **适用场景:** 追求高点击率 (CTR) 和营销效果。
            - **逻辑:** 让 AI 在保留必选关键词的前提下，发挥创意编写符合母语习惯、更有吸引力的标题。
            """)
            
        mode = st.radio(
            "选择生成模式",
            ("Mode A (严格模式)", "Mode B (营销模式)"),
            index=1,
            help="选择 'Mode A' 进行严格格式化，或选择 'Mode B' 以获得更好的点击率。"
        )
        selected_mode = "Mode A" if "Mode A" in mode else "Mode B"
        
        # Generation Count
        num_titles = st.slider("每个产品生成标题数量", 1, 10, 5)

        # History Management
        st.divider()
        st.subheader("🔍 历史库管理")
        stats = history_manager.get_stats()
        st.caption(f"当前历史库已有标题: {stats['total_titles']} 条")
        if st.button("清除历史库 (Clear History)", type="secondary"):
             history_manager.clear_history()
             history_manager.save_history()
             st.toast("历史库已清空")
             st.rerun()

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
                    prompt = build_prompt(row, selected_mode, extra_context=performance_context)
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

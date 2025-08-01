import streamlit as st
import time
import base64
import os
from pathlib import Path

# pip install streamlit-lottie
from streamlit_lottie import st_lottie
import requests

import sys

import toml
from datetime import datetime
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import atexit


# ---------- 路径配置 ----------
# 获取当前工作目录
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

from src.agents.coordinator_agent import CoordinatorAgent
from src.formats.latex.utils import get_profect_dirs, batch_download_arxiv_tex, extract_compressed_files, get_arxiv_category, extract_arxiv_ids_V2
from src.formats.latex.prompts import init_prompts
config_dir = os.path.join(base_dir, "config")
os.makedirs(config_dir, exist_ok=True)
            
# ---------- 页面配置 ----------

st.set_page_config(
    page_title="LaTeXTrans",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
)

# 添加侧边栏宽度设置
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        width: 350px !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------- 辅助函数 ----------
def load_config(config_path):
    """加载配置文件并返回配置字典"""
    with open(config_path, "r") as f:
        config = toml.load(f)
    return config

def language_change(source_lang, target_lang):
    '''语言转换chinese-ch'''
    if target_lang == "English":
        target_lang = "en"
    elif target_lang == "Chinese":
        target_lang = "ch"

    if source_lang == "English":
        source_lang = "en"
    elif source_lang == "Chinese":
        source_lang = "ch"
    return source_lang, target_lang

def save_config(config_file, source_lang, target_lang, Model_name, API_Key, Base_URL, tex_sources_dir, output_dir, save_name=None):
    """保存当前配置到文件"""
    # 确保配置目录存在
    os.makedirs(config_file, exist_ok=True)
    
    # 获取当前时间并格式化为字符串
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构建配置文件名
    if save_name:
        # 移除可能存在的非法字符
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        config_filename = os.path.join(config_file, f"{safe_name}.toml")
    else:
        # 如果没有提供名称，则使用当前时间戳作为文件名
        config_filename = os.path.join(config_file, f"config_{current_time}.toml")
    
    source_lang, target_lang = language_change(source_lang, target_lang)

    config = {
        "sys_name": "LaTexTrans",
        "version": "0.0.1",
        "target_language": target_lang if target_lang else "ch",
        "source_language": source_lang if source_lang else "en",
        "paper_list": [arxiv_id] if arxiv_id else [],
        "tex_sources_dir": tex_sources_dir.replace("\\", "\\\\"),
        "output_dir": output_dir.replace("\\", "\\\\"),
        "category" : {},
        "update_term": "False",
        "mode": 0,
        "user_term": "",
        "llm_config": {
            "model": Model_name,
            "api_key": API_Key,
            "base_url": Base_URL,
        }
    }
    # 手动构造 TOML 字符串，避免空字典变成 [category]
    toml_str = f"""
sys_name = "{config['sys_name']}"
version = "{config['version']}"
target_language = "{config['target_language']}"
source_language = "{config['source_language']}"
paper_list = {config['paper_list']}
tex_sources_dir = "{config['tex_sources_dir']}"
output_dir = "{config['output_dir']}"
category = {{}}
update_term = "{config['update_term']}"
mode = {config['mode']}
user_term = "{config['user_term']}"

[llm_config]
model = "{config['llm_config']['model']}"
api_key = "{config['llm_config']['api_key']}"
base_url = "{config['llm_config']['base_url']}"
"""
        
    with open(config_filename, "w") as f:
        f.write(toml_str.strip())  # 写入手动构造的 TOML 字符串
    
    return config_filename
    # with open(config_filename, "w") as f:
    #     toml.dump(config, f)
    # return config_filename

def update_config(target_lang, source_lang, arxiv_id, tex_sources_dir, output_dir, update_term, mode, user_term, model_name, api_key, base_url):
    '''更新当前显示文件'''
    # ---------- 写入config.toml ----------
    source_lang, target_lang = language_change(source_lang, target_lang)

    if update_term == True:
        update_term = "True"
    else:
        update_term = "False"
    


    config = {
        "sys_name": "LaTeXTrans",
        "version": "0.1.0",
        "target_language": target_lang,
        "source_language": source_lang,
        "paper_list": [arxiv_id] if arxiv_id else [],
        "tex_sources_dir": tex_sources_dir.replace("\\", "\\\\"),
        "output_dir": output_dir.replace("\\", "\\\\"),
        "category": {},
        "update_term": update_term,
        "mode": mode,
        "user_term":user_term.replace("\\", "\\\\"),
        "llm_config": {
            "model": model_name,
            "api_key": api_key,
            "base_url": base_url
        }
    }

    # 手动构造 TOML 字符串，避免空字典变成 [category]
    toml_str = f"""
sys_name = "{config['sys_name']}"
version = "{config['version']}"
target_language = "{config['target_language']}"
source_language = "{config['source_language']}"
paper_list = {config['paper_list']}
tex_sources_dir = "{config['tex_sources_dir']}"
output_dir = "{config['output_dir']}"
category = {{}}
update_term = "{config['update_term']}"
mode = {config['mode']}
user_term = "{config['user_term']}"

[llm_config]
model = "{config['llm_config']['model']}"
api_key = "{config['llm_config']['api_key']}"
base_url = "{config['llm_config']['base_url']}"
"""
    save_path = os.path.join(config_dir, "default.toml")
    with open(save_path, "w") as f:
        f.write(toml_str.strip())  # 写入手动构造的 TOML 字符串
    

    # save_path = os.path.join(config_dir, "default.toml")
    # with open(save_path, "w") as f:
    #     toml.dump(config, f)

def choose(mode):
    if mode == "base_model":
        return 0
    elif mode == "model with your term pairs":
        return 2
    

def encode_pdf_base64(pdf_path):
    '''编码pdf'''
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def st_display_pdf_single(pdf_path, selected_pdf):
    '''单栏显示pdf'''
    st.markdown(f"### preview:{selected_pdf}")
    with st.spinner("Loading..."):
        pdf_viewer(
            pdf_path,
            width=700,
            height=800,
            key="pdf_viewer"
        )
    file_size = os.path.getsize(pdf_path) / (1024*1024)
    st.caption(f"file: {selected_pdf} size: {file_size:.2f} MB")
    
def st_display_pdf_double(pdf_source_dir, pdf_target_dir, selected_source, selected_target):
    '''双栏对比显示pdf'''
    col1, col2 = st.columns([0.5, 0.5])
                
    with col1:
        source_path = os.path.join(pdf_source_dir, selected_source)
        with st.spinner("Loading original PDF..."):
            pdf_viewer(
                source_path,
                width=600,
                height=900,
                key="pdf_viewer_source"
            )
    
    with col2:
        target_path = os.path.join(pdf_target_dir, selected_target)
        with st.spinner("Loading translated PDF..."):
            pdf_viewer(
                target_path,
                width=600,
                height=900,
                key="pdf_viewer_target"
            )
    # 显示文件大小信息
    source_size = os.path.getsize(os.path.join(pdf_source_dir, selected_source)) / (1024 * 1024)
    target_size = os.path.getsize(os.path.join(pdf_target_dir, selected_target)) / (1024 * 1024)
    st.caption(f"Original: {selected_source} ({source_size:.2f} MB) | Translated: {selected_target} ({target_size:.2f} MB)")

def clearup():
    '''临时文件清理'''
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
        st.write(f"Cleared temporary file:{temp_file_path}.")
# ---------- Lottie 动画 URL 加载 ----------
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        return None


# ---------- 初始化会话状态 ----------
if 'default_config' not in st.session_state:
    st.session_state.default_config = {}

# 初始化默认值
default_model_name = st.session_state.default_config.get("model", "")
default_api_key = st.session_state.default_config.get("api_key", "")
default_base_url = st.session_state.default_config.get("base_url", "")
default_tex_sources_dir = st.session_state.default_config.get("tex_sources_dir", "")
default_output_dir = st.session_state.default_config.get("output_dir", "")

# ---------- 标题 ----------
st.markdown("""
<style>
.title-glow {
  font-size: 3em;
  font-weight: bold;
  text-align: center;
  background: linear-gradient(-45deg, #ff8a00, #e52e71, #9b00ff, #00eaff);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: rainbow 5s ease infinite, glow 2s ease-in-out infinite alternate;
}

@keyframes rainbow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes glow {
  from { text-shadow: 0 0 10px #ff8a00; }
  to   { text-shadow: 0 0 20px #e52e71; }
}
</style>

<h1 class='title-glow'>LaTeXTrans 🚀</h1>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------- 主页设置 ----------



# ---------- 侧边栏设置 ----------
with st.sidebar:
    st.header("LaTeXTrans 🚀")

    with st.expander("some help"):
        st.subheader("Attention!!!")
        st.text("Our paper address is associated with Arxiv-id. If you want to read other translated papers, please modify the Arxiv-id area to change the viewing folder (our input path naming format=user input path+Arxiv-id, output path naming format=user input output path+ch_ Arxiv-id)")
        st.text("Please pay attention to the question mark prompts for each module")

    # 使用 st.session_state 来初始化 widget 值
    arxiv_id = st.text_input("Please enter ArXiv ID:",
                            placeholder="e.g., 2305.12345",
                            help="Enter the ArXiv ID of the paper you want to translate.")
    
    arxiv_id = extract_arxiv_ids_V2(arxiv_id)

    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox("Source Language",
                                  ["English", "Chinese", "Japanese", "Korean"],
                                  index=0,
                                  help="Select the source language of the paper.")

    with col2:
        target_lang = st.selectbox("Target Language",
                                  ["Chinese", "English", "Japanese", "Korean"],
                                  index=0,
                                  help="Select the target language for translation.")
        
    update_term = st.checkbox("Update Term Pairs",
                             help="Update term pairs in the paper(Better performance comes with more tokens)",
                             value=False)
    
    mode_1 = st.selectbox("Translation Mode",
                        ["base_model", "model with your term pairs"],
                        index=0,
                        help="Select the translation mode.")
    mode = choose(mode_1)

    
    term = st.selectbox("Term Pairs",
                       ["Use default Term", "Use MyTerm"],
                       index=0,
                       help="Select term pairs. If you want to use your own term pairs, please choose 'Use MyTerm' and upload your file.")
    if term == "Use MyTerm":
        updated_file = st.file_uploader("Upload your Term file",
                                      type=["csv"],
                                      help="Please upload your Term file (format like 'english,chinese').")
        if updated_file:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w+b")
            temp_file_path = tmp.name

            tmp.write(updated_file.getvalue())
            tmp.close()

            st.session_state.default_config["user_term"] = temp_file_path
            # st.write(f"Uploaded Term file:{temp_file_path}.")
            atexit.register(clearup)

        else:
            temp_file_path = ""
            st.warning("Please upload your Term file.")
    else:
        temp_file_path = ""

    with st.expander("🔑 Model Settings", expanded=False):
        model_name = st.text_input("Model Name",
                                value=default_model_name,
                                placeholder="Such as: DeepSeek-R1",
                                key="model")
        api_key = st.text_input("API Key", 
                            value=default_api_key,
                            placeholder="Your API Key", 
                            type="password",
                            key="api_key")
        base_url = st.text_input("Base URL", 
                                value=default_base_url,
                                placeholder="Such as: https://api.deepseek.com/v1",
                                key="base_url")
    
    with st.expander("📁 FIle setting", expanded=False):
        # 选择下载文件和翻译文件的保存位置
        tex_sources_dir = st.text_input("Projects Directory",
                                    value=default_tex_sources_dir,
                                    key="tex_sources_dir",
                                    help="Directory to store downloaded LaTeX source files.")

        output_dir = st.text_input("Output Directory",
                                    value=default_output_dir,
                                    key="output_dir",
                                    help="Directory to store output files.")

    update_config(target_lang, source_lang, arxiv_id, tex_sources_dir, output_dir, update_term, mode, temp_file_path, model_name, api_key, base_url)

    # 配置文件保存与导入
    with st.expander("⚙️ Config setting", expanded=False):
        config_file = st.text_input("Config File", 
                                    placeholder="please input your config file path", 
                                    key="config_file")

        if config_file:
            config_files = [f for f in os.listdir(config_file) if f.endswith(".toml")]
            # 创建下拉选择
            selected_config = st.selectbox("Load Config",
                                            ["Select a config file"] + config_files,
                                            index=0 if config_files else None,
                                            help="Select a configuration file to load.")

            if st.button("Load Config", 
                        use_container_width=True,
                        help="Load the selected configuration file and update the settings.",
                        disabled=not config_files):
                if selected_config and selected_config != "Select a config file":
                    try:
                        config_path = os.path.join(config_file, selected_config)
                        config = load_config(config_path)
                        
                        # 更新会话状态中的默认值
                        st.session_state.default_config = {
                            "model": config.get("llm_config",{}).get("model", ""),
                            "api_key": config.get("llm_config",{}).get("api_key", ""),
                            "base_url": config.get("llm_config",{}).get("base_url", ""),
                            "tex_sources_dir": config.get("tex_sources_dir", ""),
                            "output_dir": config.get("output_dir", "")
                        }
                        
                        # 使用 st.rerun() 重新加载页面以应用新配置
                        st.rerun()
                    except Exception as e:
                        st.error(f"加载配置失败: {e}")
                else:
                    st.warning("请选择一个有效的配置文件")

        save_name = st.text_input("Config Name",
                                    placeholder="Enter a name for your config",
                                    help="Enter a name for your configuration file.")
        if st.button("Save Config", use_container_width=True,
                    help="Save your configuration settings to a file."):
            try:
                saved_path = save_config(config_file,source_lang, target_lang, model_name, api_key, base_url, tex_sources_dir, output_dir, save_name=save_name if save_name else None)
                st.success(f"配置已保存到: {saved_path}")
                # 更新默认配置
                st.session_state.default_config = {
                    "model": model_name,
                    "api_key": api_key,
                    "base_url": base_url,
                    "tex_sources_dir": tex_sources_dir,
                    "output_dir": output_dir
                }
            except Exception as e:
                st.error(f"保存配置失败: {e}")
    
    


    # 翻译按钮
    if st.button("🔁 Translate Now", use_container_width=True):
        st.session_state['translating'] = True
    else:
        st.session_state['translating'] = False


lottie_ai = load_lottie_url("https://assets7.lottiefiles.com/packages/lf20_nnpnmv0b.json")

view_enable = True

# ---------- 翻译按钮 ----------
if st.session_state.get("translating", False):
    if not arxiv_id:
        st.warning("⚠️ Please enter a valid ArXiv ID!")
    elif source_lang == target_lang:
        st.warning("⚠️ Source and target language cannot be the same.")
    else:
        if lottie_ai:
            st_lottie(lottie_ai, height=200, key="thinking")
        else:
            st.info("🤖 Translating...")

        st.info(f"Translating `{arxiv_id}` from {source_lang} to {target_lang}...")



        # # 1.下载论文

        config_path = os.path.join(config_dir, "default.toml")
        config = load_config(config_path)
        projects_dir = config.get("tex_sources_dir", default_tex_sources_dir)
        output_dir = config.get("output_dir", default_output_dir)
        os.makedirs(projects_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        if arxiv_id:
            # 检查本地是否存在id的论文
            arxiv_dir = os.path.join(projects_dir, arxiv_id)
            if os.path.exists(arxiv_dir):
                st.info(f"📁 arXiv paper {arxiv_id} already exists locally, skipping download.")
                projects = [arxiv_dir]

            else:
                projects = batch_download_arxiv_tex([arxiv_id], projects_dir)

            config["category"] = get_arxiv_category([arxiv_id])
            extract_compressed_files(projects_dir)
        else:
            st.error("⚠️ No paper list provided. Using existing projects in the specified directory.")
            extract_compressed_files(projects_dir)
            projects = get_profect_dirs(projects_dir)
            if not projects:
                st.error("❌ No projects found. Check 'tex_sources_dir' and 'paper_list' in config.")

        # 2.翻译 and 生成
        for project_dir in projects:
            try:
                # init_prompts(source_lang=config["source_language"], target_lang=config["target_language"])
                LaTexTrans = CoordinatorAgent(
                    config=config,
                    project_dir=project_dir,
                    output_dir=output_dir
                )
                LaTexTrans.workflow_latextrans()
            except Exception as e:
                st.error(f"❌ Error processing project {os.path.basename(project_dir)}: {e}")
                continue
        st.balloons()

# ---------- 预览 ----------
if view_enable:
    # ---------- PDF预览选项卡 ----------

    tab1, tab2 = st.tabs(["📄 Single column preview", "📖 Double column comparison"])

    with tab1:
        pdf_target_dir = os.path.join(output_dir, f"ch_{arxiv_id}")
        if not os.path.exists(pdf_target_dir):
            st.warning("No PDF file found.")
            st.stop()
        
        pdf_files = [f for f in os.listdir(pdf_target_dir) if f.endswith(".pdf")]
        if not pdf_files:
            st.warning("No PDF file found.")
            st.stop()
        
        selected_pdf = st.selectbox("Select a PDF file", 
                                    pdf_files,
                                    index=0,
                                    help="Select a PDF file to view.")
        preview_button = st.button("▶️ Start Preview", key="preview_button_single")
        if selected_pdf and preview_button:
            pdf_path = os.path.join(pdf_target_dir, selected_pdf)
            st_display_pdf_single(pdf_path, selected_pdf)
    
    with tab2:
        pdf_sources_dir = os.path.join(tex_sources_dir, f"{arxiv_id}")
        pdf_target_dir = os.path.join(output_dir, f"ch_{arxiv_id}")

        if not os.path.exists(pdf_target_dir) or not os.path.exists(pdf_sources_dir):
            st.warning("No PDF file found.")
            st.stop()
        
        source_pdf_files = [f for f in os.listdir(pdf_sources_dir) if f.endswith(".pdf")]
        target_pdf_files = [f for f in os.listdir(pdf_target_dir) if f.endswith(".pdf")]

        if not source_pdf_files or not target_pdf_files:
            st.warning("No PDF file found in souyrce or target directory.")
            st.stop()
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original PDF**")
            selected_source = st.selectbox("Select a PDF file", 
                                            source_pdf_files,
                                            index=0,
                                            key="source_pdf_select")
        with col2:
            st.markdown("**Translated PDF**")
            selected_target = st.selectbox("Select a PDF file", 
                                        target_pdf_files,
                                        index=0,
                                        key="translated_pdf_select")
        preview_button_double = st.button("▶️ Start Comparison", 
                                          key="preview_button_double")
        
        if selected_source and selected_target and preview_button_double:
            st_display_pdf_double(pdf_sources_dir, pdf_target_dir, selected_source, selected_target)
        else:
            st.warning("Please select two PDF files and click the '▶️ Start Comparison' button.")


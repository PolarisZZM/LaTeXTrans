import toml
import argparse
import os
import sys
from src.agents.coordinator_agent import CoordinatorAgent
from src.formats.latex.utils import get_profect_dirs, batch_download_arxiv_tex, extract_compressed_files, get_arxiv_category, extract_arxiv_ids
from src.formats.latex.prompts import *
import subprocess
import streamlit
from tqdm import tqdm
from pathlib import Path

base_dir = os.getcwd()
sys.path.append(base_dir)

def main():
    """
    Main function to run the LaTeXTrans application.
    Allows overriding paper_list from command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config/default.toml", help="Path to the config TOML file.")
    #parser.add_argument("paper_ids", nargs="*", help="Optional list of arXiv paper IDs to override config.")
    parser.add_argument("--model", type=str, default="", help="Model for translating.")
    parser.add_argument("--url", type=str, default="", help="Model url.")
    parser.add_argument("--key", type=str, default="", help="Model key.")
    parser.add_argument("--Arxiv", type=str, default="", help="Arxiv paper ID.")
    parser.add_argument("--GUI", "-g", action="store_true", help="Interact with GUI.")
    parser.add_argument("--mode", type=int, default=2, help="Translate mode.")
    parser.add_argument("--update_term", type=str, default="False", help="Update term or not.")
    parser.add_argument("--tl", type=str, default="ch", help="Target language.")
    parser.add_argument("--sl", type=str, default="en", help="Source language.")
    parser.add_argument("--ut", type=str, default="", help="User's term dict.")
    parser.add_argument("--output", type=str, default="", help="output directory.")
    parser.add_argument("--source", type=str, default="", help="tex source directory.")
    parser.add_argument("--save_config", type=str, default="", help="Path to save config.")
    parser.add_argument("--valid", "-v", action="store_true", help="use valid agent.")
    parser.add_argument("--filter", "-f", action="store_true", help="use filter agent.")




    args = parser.parse_args()

    if args.GUI:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, "src", "UI", "UI.py")
        subprocess.run(["streamlit", "run", ui_path])
        return 0

    # args_dict = vars(args)
    config = toml.load(args.config)

    if args.url:
        config["llm_config"]["base_url"] = args.url
    if args.Arxiv:
        config["paper_list"].append(args.Arxiv)
    if args.model:
        config["llm_config"]["model"] = args.model
    if args.key:
        config["llm_config"]["api_key"] = args.key
    if args.mode:
        config["mode"] = args.mode
    if args.update_term:
        config["update_term"] = args.update_term
    if args.tl:
        config["target_language"] = args.tl
    if args.sl:
        config["source_language"] = args.sl
    if args.source:
        config["tex_sources_dir"] = args.source
    if args.output:
        config["output_dir"] = args.output
    if args.ut:
        config["user_term"] = args.ut

    #init_prompts(config["source_language"], config["target_language"])


    # override paper_list if user passed in IDs via CLI
    # 之后设置参数时，config和args的传递参考这个
    # if args.paper_ids:
    #     config["paper_list"] = args.paper_ids

    paper_list = config.get("paper_list", [])
    paper_list = extract_arxiv_ids(paper_list)
    projects_dir = os.path.join(base_dir, config.get("tex_sources_dir", "tex-source"))
    output_dir = os.path.join(base_dir, config.get("output_dir", "outputs"))

    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    if paper_list:
        projects = batch_download_arxiv_tex(paper_list, projects_dir)
        if not config["user_term"] or args.mode == "0":
            config["category"] = get_arxiv_category(paper_list)
            # print(config["category"])
        extract_compressed_files(projects_dir)
    else:
        print("⚠️ No paper list provided. Using existing projects in the specified directory.")
        extract_compressed_files(projects_dir)
        projects = get_profect_dirs(projects_dir)
        if not projects:
            raise ValueError("❌ No projects found. Check 'tex_sources_dir' and 'paper_list' in config.")



    # 检测并选择LaTeX发行版
    from src.formats.latex.utils import detect_tex_distributions, select_tex_distribution
    
    print("🔍 Detecting LaTeX distributions...")
    distributions = detect_tex_distributions()
    
    if not distributions:
        print("❌ No LaTeX distributions found. Please install TeX Live or MiKTeX.")
        return 1
    
    selected_latexmk_path = None
    if len(distributions) == 1:
        # 只有一个发行版，自动选择
        selected_latexmk_path = list(distributions.values())[0]
        print(f"✅ Auto-selected: {list(distributions.keys())[0]}")
    else:
        # 多个发行版，让用户选择
        selected_latexmk_path = select_tex_distribution(distributions)
        if not selected_latexmk_path:
            print("❌ No LaTeX distribution selected. Exiting.")
            return 1

    for project_dir in tqdm(projects, desc="Processing projects", unit="project"):

        try:

            LaTexTrans = CoordinatorAgent(
                config=config,
                project_dir=project_dir,
                output_dir=output_dir,
                latexmk_path=selected_latexmk_path  # <--- 新增参数
            )
            LaTexTrans.workflow_latextrans()
        except Exception as e:
            print(f"❌ Error processing project {os.path.basename(project_dir)}: {e}")
            continue

    config["paper_list"] = []
    config["category"] = {}
    if args.save_config:
        toml_str = toml.dumps(config)
        print(toml_str)
        toml_str = toml_str.replace("[category]", "category = {}")
        print(toml_str)
        config_path = Path(args.save_config) / "Myconfig.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            f.write(toml_str)
        print(f"save config to {config_path}!")



if __name__ == "__main__":
    main()


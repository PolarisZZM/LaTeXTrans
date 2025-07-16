import toml
import argparse
import os
import sys
from src.agents.coordinator_agent import CoordinatorAgent
from src.formats.latex.utils import (
    get_profect_dirs, 
    batch_download_arxiv_tex, 
    extract_compressed_files,
    detect_tex_distributions, 
    select_tex_distribution # 导入新函数
)
from tqdm import tqdm

base_dir = os.getcwd()
sys.path.append(base_dir)

def main():
    """
    Main function to run the LaTeXTrans application.
    Allows overriding paper_list from command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config/default.toml", help="Path to the config TOML file.")
    parser.add_argument("paper_ids", nargs="*", help="Optional list of arXiv paper IDs to override config.")
    args = parser.parse_args()

    config = toml.load(args.config)

    # --- 新增的发行版选择逻辑 ---
    all_distributions = detect_tex_distributions()
    selected_latexmk_path = None

    if not all_distributions:
        print("❌ Error: No LaTeX distribution (like TeX Live or MiKTeX) with 'latexmk' was found on your system.")
        print("Please install a LaTeX distribution and ensure it's in your system's PATH.")
        return # 退出程序

    if len(all_distributions) > 1:
        print("Found multiple LaTeX distributions. Please select one to use for all projects in this run.")
        selected_latexmk_path = select_tex_distribution(all_distributions)
        if not selected_latexmk_path:
            print("No distribution selected. Exiting.")
            return
    else:
        selected_latexmk_path = list(all_distributions.values())[0]
        dist_name = list(all_distributions.keys())[0]
        print(f"✅ Automatically selected LaTeX distribution: {dist_name}")
    
    print("-" * 50)
    # --- 逻辑结束 ---

    # override paper_list if user passed in IDs via CLI
    if args.paper_ids:
        config["paper_list"] = args.paper_ids

    paper_list = config.get("paper_list", [])
    projects_dir = os.path.join(base_dir, config.get("tex_sources_dir", "tex source"))
    output_dir = os.path.join(base_dir, config.get("output_dir", "outputs"))

    if paper_list:
        projects = batch_download_arxiv_tex(paper_list, projects_dir)
        extract_compressed_files(projects_dir)
    else:
        print("⚠️ No paper list provided. Using existing projects in the specified directory.")
        extract_compressed_files(projects_dir)
        projects = get_profect_dirs(projects_dir)
        if not projects:
            raise ValueError("❌ No projects found. Check 'tex_sources_dir' and 'paper_list' in config.")

    for project_dir in tqdm(projects, desc="Processing projects", unit="project"):
        try:
            # 将选择的发行版路径传递给 CoordinatorAgent
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

if __name__ == "__main__":
    main()
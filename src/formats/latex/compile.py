from typing import List, Dict, Any
import re
import os
import subprocess
import shutil
# 导入现在位于 utils 中的函数
from .utils import find_main_tex_file, detect_tex_distributions, select_tex_distribution

class LaTexCompiler:
    # 修改构造函数以接收预选的 latexmk_path
    def __init__(self, output_latex_dir: str, latexmk_path: str):
        self.output_latex_dir = output_latex_dir
        # initial_latexmk_path 是在 main.py 中选择的默认路径，不会改变
        self.initial_latexmk_path = latexmk_path
        # latexmk_path 是当前编译任务使用的路径，可能会在重试时改变
        self.latexmk_path = latexmk_path

    # _select_distribution 函数已被移除，其功能移至 utils.py

    def _ask_and_switch_distribution(self, remaining_distributions: Dict[str, str]) -> str:
        """Asks the user to switch, lets them select a new distribution, and returns the new path."""
        print("\nDo you want to try compiling with a different LaTeX distribution?")
        while True:
            switch_choice = input("Enter 'yes' to switch, 'no' to abort: ").lower().strip()
            if switch_choice in ['yes', 'no']:
                break
            print("Invalid input. Please enter 'yes' or 'no'.")

        if switch_choice == 'no':
            return None

        # 用户想要切换，从剩余发行版中选择
        new_path = select_tex_distribution(remaining_distributions)
        return new_path

    def compile(self):
        """
        Compile the LaTeX document using the pre-selected distribution,
        with an option to switch to another on failure.
        """
        # --- 核心逻辑改动 ---
        # 确保每个项目开始时，都使用最初在 main.py 中选择的发行版
        self.latexmk_path = self.initial_latexmk_path
        
        if not self.latexmk_path:
            print("❌ Error: No LaTeX distribution path was provided to the compiler.")
            return None

        all_distributions = detect_tex_distributions()
        
        while self.latexmk_path:
            selected_dist_name = next((name for name, path in all_distributions.items() if path == self.latexmk_path), "Unknown")
            
            distributions_to_try_next = all_distributions.copy()
            if selected_dist_name in distributions_to_try_next:
                del distributions_to_try_next[selected_dist_name]

            # ... (清理、查找 tex 文件等逻辑保持不变) ...
            print(f"🧹 Cleaning up previous build directories before attempting with '{selected_dist_name}'...")
            compile_out_dir_pdflatex = os.path.join(self.output_latex_dir, "build_pdflatex")
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            if os.path.exists(compile_out_dir_pdflatex): shutil.rmtree(compile_out_dir_pdflatex)
            if os.path.exists(compile_out_dir_xelatex): shutil.rmtree(compile_out_dir_xelatex)
            tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
            if not tex_file_to_compile:
                print("⚠️ Warning: There is no main tex file to compile in this directory.")
                return None

            # Attempt 1: pdflatex
            print(f"\nAttempting compilation with pdflatex using '{selected_dist_name}'...⏳")
            return_code_pdflatex = self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
            
            if return_code_pdflatex == 0:
                main_tex_base = os.path.splitext(os.path.basename(tex_file_to_compile))[0]
                source_pdf_path = os.path.join(compile_out_dir_pdflatex, f"{main_tex_base}.pdf")
                if os.path.exists(source_pdf_path):
                    dest_dir = os.path.dirname(self.output_latex_dir) # PDF is copied to the parent of the build dir
                    dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                    print(f"✅ Successfully generated PDF with pdflatex!")
                    shutil.copy(source_pdf_path, dest_pdf_path)
                    return dest_pdf_path

            # Attempt 2: xelatex
            print(f"⚠️ Failed to generate PDF with pdflatex. Retrying with xelatex using '{selected_dist_name}'...⏳")
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            return_code_xelatex = self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
            
            if return_code_xelatex == 0:
                main_tex_base = os.path.splitext(os.path.basename(tex_file_to_compile))[0]
                source_pdf_path = os.path.join(compile_out_dir_xelatex, f"{main_tex_base}.pdf")
                if os.path.exists(source_pdf_path):
                    dest_dir = os.path.dirname(self.output_latex_dir)
                    dest_pdf_path = os.path.join(dest_dir, f"{os.path.basename(dest_dir)}.pdf")
                    print(f"✅ Successfully generated PDF with xelatex!")
                    shutil.copy(source_pdf_path, dest_pdf_path)
                    return dest_pdf_path

            # Both engines failed with the current distribution
            print(f"❌ Compilation failed with both pdflatex and xelatex using '{selected_dist_name}'.")

            if not distributions_to_try_next:
                print("No other LaTeX distributions to try.")
                self.latexmk_path = None # End loop
            else:
                # This will use the temporary choice for the *next iteration of this while loop only*
                self.latexmk_path = self._ask_and_switch_distribution(distributions_to_try_next)

        # Loop has ended, compilation failed for this project
        print("\nCompilation failed. Please check the logs for more details.")
        # ... (log file printing logic remains the same) ...
        return None

    # --- 其他编译方法保持不变 ---
    # ... 请确保将您原始文件中的 compile_ja, _compile_with_pdflatex, _compile_with_xelatex, _compile_with_lualatex 完整地复制到这里 ...
    def compile_ja(self):
        """
        Compile the LaTeX document . """
        tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
        if not tex_file_to_compile:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None
        print("Start compiling with lualatex...⏳")
        compile_out_dir_lualatex = os.path.join(self.output_latex_dir, "build_lualatex")
        return_code_lualatex = self._compile_with_lualatex(tex_file_to_compile, compile_out_dir_lualatex, engine="lualatex")
        pdf_files = [os.path.join(compile_out_dir_lualatex, file) for file in os.listdir(compile_out_dir_lualatex) if file.lower().endswith('.pdf')]
        if pdf_files:

            print(f"✅  Successfully generated PDF file !") 
            return pdf_files[0]
        else:
            print(f"⚠️  Failed to generate PDF with xelatex. Please check the log.")
            # log_files_xelatex = [os.path.join(compile_out_dir_xelatex, file) for file in os.listdir(compile_out_dir_xelatex) if file.lower().endswith('.log')]
            log_files_lualatex = [os.path.join(compile_out_dir_lualatex, file) for file in os.listdir(compile_out_dir_lualatex) if file.lower().endswith('.log')]
            if log_files_lualatex:
                print(f"📄 Log files for pdflatex: {log_files_lualatex}")
            return None


    def _compile_with_pdflatex(self,
                               tex_file: str, 
                              out_dir: str, 
                              engine: str = "pdflatex"):
        
        source_dir = os.path.dirname(tex_file)
        main_tex_filename = os.path.basename(tex_file)

        try:
            shutil.copytree(source_dir, out_dir, ignore=shutil.ignore_patterns('build_*'))
        except Exception as e:
            print(f"❌ Error copying source files to build directory: {e}")
            return -1

        tex_file_in_build_dir = os.path.join(out_dir, main_tex_filename)
        
        try:
            with open(tex_file_in_build_dir, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except FileNotFoundError:
            print(f"❌ Error: Main TeX file not found at {tex_file_in_build_dir}")
            return -1

        pdflatex_packages = "\\usepackage{CJKutf8}\n\\usepackage[utf8]{inputenc}"
        modified_content = original_content.replace("%%CHINESE_PACKAGE_PLACEHOLDER%%", pdflatex_packages)
        
        modified_content = re.sub(r"(\\begin\{document\})", r"\1\n\\begin{CJK*}{UTF8}{gbsn}", modified_content, count=1)
        modified_content = re.sub(r"(\\end\{document\})", r"\\end{CJK*}\n\1", modified_content, count=1)
        modified_content = modified_content.replace(r'\(s_{\max}}\)', r'\(s_{\max}\)')

        with open(tex_file_in_build_dir, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        cmd = [ self.latexmk_path, f"-{engine}", "-interaction=nonstopmode", f"-file-line-error", f"-synctex=1", main_tex_filename ]
        
        cwd = out_dir
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)

        if result.returncode != 0:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            if stdout.strip(): print(f"--- {engine} stdout ---\n{stdout}\n---")
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stderr.strip(): print(f"--- {engine} stderr ---\n{stderr}\n---")
            
        return result.returncode

    def _compile_with_xelatex(self,
                              tex_file: str, 
                              out_dir: str, 
                              engine: str = "xelatex"):
        
        source_dir = os.path.dirname(tex_file)
        main_tex_filename = os.path.basename(tex_file)

        try:
            shutil.copytree(source_dir, out_dir, ignore=shutil.ignore_patterns('build_*'))
        except Exception as e:
            print(f"❌ Error copying source files to build directory: {e}")
            return -1

        tex_file_in_build_dir = os.path.join(out_dir, main_tex_filename)
        
        try:
            with open(tex_file_in_build_dir, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except FileNotFoundError:
            print(f"❌ Error: Main TeX file not found at {tex_file_in_build_dir}")
            return -1

        xelatex_package = "\\usepackage[fontset=fandol,UTF8]{ctex}"
        modified_content = original_content.replace("%%CHINESE_PACKAGE_PLACEHOLDER%%", xelatex_package)
        modified_content = modified_content.replace(r'\(s_{\max}}\)', r'\(s_{\max}\)')

        with open(tex_file_in_build_dir, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        cmd = [ self.latexmk_path, f"-{engine}", "-interaction=nonstopmode", f"-file-line-error", f"-synctex=1", main_tex_filename ]
        
        cwd = out_dir
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"
        
        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        
        return result.returncode


    def _compile_with_lualatex(self,
                              tex_file: str, 
                              out_dir: str, 
                              engine: str = "lualatex"):
        
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = [ self.latexmk_path, f"-{engine}", "-interaction=nonstopmode", f"-outdir={out_dir}", f"-file-line-error", f"-synctex=1", tex_file ]
        cwd = os.path.dirname(tex_file)

        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"
        
        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)

        if result.returncode != 0:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            if stdout.strip(): print(f"--- {engine} stdout ---\n{stdout}\n---")
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stderr.strip(): print(f"--- {engine} stderr ---\n{stderr}\n---")
            
        return result.returncode
from typing import List, Dict, Any
import re
import os
import subprocess
from .utils import *

class LaTexCompiler:
    def __init__(self, output_latex_dir: str):
        self.output_latex_dir = output_latex_dir
        self.latexmk_path = None

    def _select_distribution(self, distributions: Dict[str, str]) -> str:
        """Prompts the user to select a LaTeX distribution and returns the path to latexmk."""
        print("\nMultiple LaTeX distributions found. Please choose which one to use for compilation:")
        
        # Create a numbered list of distributions
        dist_list = list(distributions.items())
        for i, (name, path) in enumerate(dist_list):
            print(f"  [{i+1}] {name} ({path})")
        
        choice = -1
        while choice < 1 or choice > len(dist_list):
            try:
                raw_choice = input(f"Enter your choice (1-{len(dist_list)}): ")
                choice = int(raw_choice)
                if not (1 <= choice <= len(dist_list)):
                    print("Invalid choice. Please try again.")
            except (ValueError, EOFError):
                print("Invalid input. Please enter a number.")
        
        # Return the full path of the selected latexmk
        return dist_list[choice-1][1]

    def compile(self):
        """
        Compile the LaTeX document.
        """
        distributions = detect_tex_distributions()
        if not distributions:
            print("❌ Error: No LaTeX distribution (like TeX Live or MiKTeX) with 'latexmk' was found on your system.")
            print("Please install a LaTeX distribution and ensure it's in your system's PATH.")
            return None

        if len(distributions) > 1:
            self.latexmk_path = self._select_distribution(distributions)
        else:
            # If only one distribution, use it automatically
            self.latexmk_path = list(distributions.values())[0]
            print(f"✅ Automatically selected LaTeX distribution: {list(distributions.keys())[0]}")

        tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
        if not tex_file_to_compile:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None
        print("Start compiling with pdflatex...⏳")
        compile_out_dir_pdflatex = os.path.join(self.output_latex_dir, "build_pdflatex")
        self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
        pdf_files = [os.path.join(compile_out_dir_pdflatex, file) for file in os.listdir(compile_out_dir_pdflatex) if file.lower().endswith('.pdf')]
        if pdf_files:

            print(f"✅  Successfully generated PDF file !") 
            return pdf_files[0]
        else:
            print(f"⚠️  Failed to generate PDF with pdflatex. 🔁Retrying with xelatex...⏳") 
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
            pdf_files = [os.path.join(compile_out_dir_xelatex, file) for file in os.listdir(compile_out_dir_xelatex) if file.lower().endswith('.pdf')]
            if pdf_files:
                print(f"✅  Successfully generated PDF file !") 
                return pdf_files[0]
            else:
                print(f"⚠️  Failed to generate PDF with xelatex. Please check the log.")
                log_files_xelatex = [os.path.join(compile_out_dir_xelatex, file) for file in os.listdir(compile_out_dir_xelatex) if file.lower().endswith('.log')]
                log_files_pdflatex = [os.path.join(compile_out_dir_pdflatex, file) for file in os.listdir(compile_out_dir_pdflatex) if file.lower().endswith('.log')]
                if log_files_xelatex and log_files_pdflatex:
                    print(f"📄 Log files for pdflatex: {log_files_pdflatex}")
                    print(f"📄 Log files for xelatex: {log_files_xelatex}")
                return None
    

    def compile_ja(self):
        """
        Compile the LaTeX document .
        """
        tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
        if not tex_file_to_compile:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None
        print("Start compiling with lualatex...⏳")
        compile_out_dir_lualatex = os.path.join(self.output_latex_dir, "build_lualatex")
        self._compile_with_lualatex(tex_file_to_compile, compile_out_dir_lualatex, engine="lualatex")
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
        
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = [
            self.latexmk_path,
            f"-{engine}",                
            "-interaction=nonstopmode",   # no stop on errors
            f"-outdir={out_dir}",  
            f"-file-line-error",       
            f"-synctex=1",
            f"-f",                        # force mode
            tex_file
        ]
        cwd = os.path.dirname(tex_file)
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=cwd)
            print("✅  Compilation successful!") #compile success!

            output_path = os.path.join(self.output_latex_dir, "success.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Compilation successful\n")
                
        except subprocess.CalledProcessError as e:
            print("⚠️  Somthing went wrong during compiling with pdflatex.")
            print(f"pdflatex stderr:\n{e.stderr.decode('utf-8', errors='ignore')}")
            print(f"pdflatex stdout:\n{e.stdout.decode('utf-8', errors='ignore')}")

    def _compile_with_xelatex(self,
                              tex_file: str, 
                              out_dir: str, 
                              engine: str = "xelatex"):
        
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = [
            self.latexmk_path,
            f"-{engine}",                
            "-interaction=nonstopmode",   # no stop on errors
            f"-outdir={out_dir}",  
            f"-file-line-error",       
            f"-synctex=1",
            f"-f",                        # force mode
            tex_file
        ]
        cwd = os.path.dirname(tex_file)
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=cwd)
            print("✅  Compilation successful!") #compile success!
        except subprocess.CalledProcessError as e:
            print("⚠️  Somthing went wrong during compiling with xelatex.")
            print(f"xelatex stderr:\n{e.stderr.decode('utf-8', errors='ignore')}")
            print(f"xelatex stdout:\n{e.stdout.decode('utf-8', errors='ignore')}")


    def _compile_with_lualatex(self,
                              tex_file: str, 
                              out_dir: str, 
                              engine: str = "lualatex"):
        
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = [
            self.latexmk_path,
            f"-{engine}",                
            "-interaction=nonstopmode",   # no stop on errors
            f"-outdir={out_dir}",  
            f"-file-line-error",       
            f"-synctex=1",
            f"-f",                        # force mode
            tex_file
        ]
        cwd = os.path.dirname(tex_file)
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=cwd)
            print("✅  Compilation successful!") #compile success!

            output_path = os.path.join(self.output_latex_dir, "success.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Compilation successful\n")
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Somthing went wrong during compiling with lualatex.")
            print(f"lualatex stderr:\n{e.stderr.decode('utf-8', errors='ignore')}")
            print(f"lualatex stdout:\n{e.stdout.decode('utf-8', errors='ignore')}")

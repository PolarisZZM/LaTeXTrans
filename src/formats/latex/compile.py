from typing import List, Dict, Any
import re
import os
import subprocess
import shutil
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

        # User wants to switch, select from remaining
        print("Please choose one of the remaining distributions:")
        new_path = self._select_distribution(remaining_distributions)
        return new_path

    def compile(self):
        """
        Compile the LaTeX document, with an option to switch distribution on failure.
        """
        all_distributions = detect_tex_distributions()
        if not all_distributions:
            print("❌ Error: No LaTeX distribution (like TeX Live or MiKTeX) with 'latexmk' was found on your system.")
            print("Please install a LaTeX distribution and ensure it's in your system's PATH.")
            return None

        # Make a copy to modify
        distributions_to_try = all_distributions.copy()
        
        # Select initial distribution
        if len(distributions_to_try) > 1:
            self.latexmk_path = self._select_distribution(distributions_to_try)
        else:
            self.latexmk_path = list(distributions_to_try.values())[0]
            print(f"✅ Automatically selected LaTeX distribution: {list(distributions_to_try.keys())[0]}")
        
        while self.latexmk_path:
            # Find the name of the current distribution
            selected_dist_name = next((name for name, path in all_distributions.items() if path == self.latexmk_path), "Unknown")
            
            # Remove the current distribution from the list of ones to try next
            if selected_dist_name in distributions_to_try:
                del distributions_to_try[selected_dist_name]

            # Clean up previous build directories to ensure a fresh compilation attempt
            print(f"🧹 Cleaning up previous build directories before attempting with '{selected_dist_name}'...")
            compile_out_dir_pdflatex = os.path.join(self.output_latex_dir, "build_pdflatex")
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            if os.path.exists(compile_out_dir_pdflatex):
                shutil.rmtree(compile_out_dir_pdflatex)
            if os.path.exists(compile_out_dir_xelatex):
                shutil.rmtree(compile_out_dir_xelatex)

            tex_file_to_compile = find_main_tex_file(self.output_latex_dir)
            if not tex_file_to_compile:
                print("⚠️ Warning: There is no main tex file to compile in this directory.")
                return None

            # Attempt 1: pdflatex
            print(f"\nAttempting compilation with pdflatex using '{selected_dist_name}'...⏳")
            compile_out_dir_pdflatex = os.path.join(self.output_latex_dir, "build_pdflatex")
            self._compile_with_pdflatex(tex_file_to_compile, compile_out_dir_pdflatex, engine="pdflatex")
            
            # Check for PDF in a more robust way
            if os.path.exists(compile_out_dir_pdflatex):
                pdf_files_pdflatex = [f for f in os.listdir(compile_out_dir_pdflatex) if f.lower().endswith('.pdf')]
                if pdf_files_pdflatex:
                    print(f"✅ Successfully generated PDF with pdflatex!")
                    return os.path.join(compile_out_dir_pdflatex, pdf_files_pdflatex[0])

            # Attempt 2: xelatex
            print(f"⚠️ Failed to generate PDF with pdflatex. Retrying with xelatex using '{selected_dist_name}'...⏳")
            compile_out_dir_xelatex = os.path.join(self.output_latex_dir, "build_xelatex")
            self._compile_with_xelatex(tex_file_to_compile, compile_out_dir_xelatex, engine="xelatex")
            
            if os.path.exists(compile_out_dir_xelatex):
                pdf_files_xelatex = [f for f in os.listdir(compile_out_dir_xelatex) if f.lower().endswith('.pdf')]
                if pdf_files_xelatex:
                    print(f"✅ Successfully generated PDF with xelatex!")
                    return os.path.join(compile_out_dir_xelatex, pdf_files_xelatex[0])

            # Both engines failed
            print(f"❌ Compilation failed with both pdflatex and xelatex using '{selected_dist_name}'.")

            if not distributions_to_try:
                print("No other LaTeX distributions to try.")
                self.latexmk_path = None # End loop
            else:
                self.latexmk_path = self._ask_and_switch_distribution(distributions_to_try)

        # Loop has ended, compilation failed
        print("\nCompilation failed. Please check the logs for more details.")
        log_files_pdflatex = []
        log_files_xelatex = []
        if 'compile_out_dir_pdflatex' in locals() and os.path.exists(compile_out_dir_pdflatex):
            log_files_pdflatex = [os.path.join(compile_out_dir_pdflatex, file) for file in os.listdir(compile_out_dir_pdflatex) if file.lower().endswith('.log')]
        if 'compile_out_dir_xelatex' in locals() and os.path.exists(compile_out_dir_xelatex):
            log_files_xelatex = [os.path.join(compile_out_dir_xelatex, file) for file in os.listdir(compile_out_dir_xelatex) if file.lower().endswith('.log')]

        if log_files_pdflatex:
            print(f"📄 Log files for pdflatex: {log_files_pdflatex}")
        if log_files_xelatex:
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

        # Create a new environment for the subprocess, prioritizing the selected distribution's path
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env)

        # A non-zero return code from latexmk doesn't always mean failure.
        # The calling method `compile` will check for PDF existence to determine success.
        # We log the output if there's a non-zero exit code for debugging purposes.
        if result.returncode == 0:
            print(f"✅  `{engine}` process completed with exit code 0.")
            output_path = os.path.join(self.output_latex_dir, "success.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Compilation successful\n")
        else:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            print(f"   This may indicate warnings or errors. Checking for PDF output...")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stdout.strip():
                print(f"--- {engine} stdout ---\n{stdout}\n---")
            if stderr.strip():
                print(f"--- {engine} stderr ---\n{stderr}\n---")

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

        # Create a new environment for the subprocess, prioritizing the selected distribution's path
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env)

        if result.returncode == 0:
            print(f"✅  `{engine}` process completed with exit code 0.")
        else:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            print(f"   This may indicate warnings or errors. Checking for PDF output...")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stdout.strip():
                print(f"--- {engine} stdout ---\n{stdout}\n---")
            if stderr.strip():
                print(f"--- {engine} stderr ---\n{stderr}\n---")


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

        # Create a new environment for the subprocess, prioritizing the selected distribution's path
        env = os.environ.copy()
        dist_bin_dir = os.path.dirname(self.latexmk_path)
        env['PATH'] = f"{dist_bin_dir}{os.pathsep}{env.get('PATH', '')}"
        
        result = subprocess.run(cmd, capture_output=True, cwd=cwd, env=env)

        if result.returncode == 0:
            print(f"✅  `{engine}` process completed with exit code 0.")
            output_path = os.path.join(self.output_latex_dir, "success.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Compilation successful\n")
        else:
            print(f"⚠️  `{engine}` process finished with non-zero exit code ({result.returncode}).")
            print(f"   This may indicate warnings or errors. Checking for PDF output...")
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            if stdout.strip():
                print(f"--- {engine} stdout ---\n{stdout}\n---")
            if stderr.strip():
                print(f"--- {engine} stderr ---\n{stderr}\n---")

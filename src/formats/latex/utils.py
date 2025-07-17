from pylatexenc.latexwalker import (
    LatexWalker, LatexMacroNode, LatexEnvironmentNode, LatexGroupNode, LatexCharsNode,
    LatexSpecialsNode, LatexMathNode
    )
from pylatexenc.latex2text import LatexNodes2Text
import os
import re
import json
import zipfile
import tarfile
from tqdm import tqdm
import regex
import subprocess
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import List
import shutil
import platform
import subprocess
import platform # 确保导入 platform
import shutil # 确保导入 shutil
from typing import Dict # 确保导入 Dict

options = r"\[[^\[\]]*?\]"
spaces = r"[ \t]*"
get_pattern_brace = lambda index: rf"\{{((?:[^{{}}]++|(?{index}))*+)\}}"

def get_pattern_command_full(name, n=None):
    pattern = rf'\\({name})'
    if n is None:
        pattern += rf'{spaces}({options})?'
        n = 1
        begin_brace = 3
    else:
        begin_brace = 2
    for i in range(n):
        tmp = get_pattern_brace(i*2+begin_brace)
        pattern += rf'{spaces}({tmp})'
    if n == 0:
        pattern += r'(?=[^a-zA-Z])'
    return pattern

def extract_compressed_files(folder_path):
    """
    Traverse the given folder and extract all compressed files (zip, tar, tar.gz, etc.).
    After extraction, delete the source compressed files.
    
    Args:
        folder_path (str): Path to the folder containing compressed files.
    """
    # paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    extract_path = os.path.join(root, file.replace('.zip', ''))
                    zip_ref.extractall(extract_path)
                    print(f"Extracted {file} to {extract_path}")
                    # paths.append(extract_path)
                os.remove(file_path)
                # print(f"Deleted source file: {file_path}")
            elif tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    extract_path = os.path.join(root, file.replace('.tar', '').replace('.gz', ''))
                    tar_ref.extractall(extract_path)
                    print(f"Extracted {file} to {extract_path}")
                    # paths.append(extract_path)
                os.remove(file_path)
                # print(f"Deleted source file: {file_path}")
    # return paths

def get_profect_dirs(folder_path):
    """
    Get a list of all subdirectories in the given folder.
    
    Args:
        folder_path (str): Path to the folder.
    
    Returns:
        list: A list of subdirectory paths.
    """
    projects = []
    for d in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, d)):
            project_path = os.path.join(folder_path, d)
            projects.append(project_path)
    return projects

def has_appendix(latex_code):
    """
    检测 LaTeX 源码中是否包含 \appendix。

    Args:
        latex_code (str): LaTeX 源码内容。

    Returns:
        bool: 如果包含 \appendix，则返回 True；否则返回 False。
    """
    # 使用正则表达式匹配 \appendix
    appendix_pattern = re.compile(r"\\appendix\b")
    # appendix_pattern = re.compile(r"\\begin\{appendix\}")
    # 搜索匹配
    return bool(appendix_pattern.search(latex_code))

def remove_appendix_content(latex_code):
    """
    删除 LaTeX 源码中 \appendix 之后的所有内容。

    Args:
        latex_code (str): LaTeX 源码内容。

    Returns:
        str: 删除 \appendix 之后内容的 LaTeX 源码。
    """
    # 使用正则表达式匹配 \appendix 及其之后的所有内容
    appendix_pattern = re.compile(r"\\appendix\b.*?(?=\\end\{document\})", re.DOTALL)
    
    # 替换匹配到的内容为空字符串
    modified_code = appendix_pattern.sub("", latex_code)
    
    return modified_code

def extract_latex_nodes(tex):
    walker = LatexWalker(tex)
    nodes, npos, nlen = walker.get_latex_nodes()
    return nodes

def extract_text_from_tex(tex):
    # convert = CustomLatexNodes2Text()
    # text = convert.latex_to_text(tex)
    text = LatexNodes2Text().latex_to_text(tex)
    return text
    
def extract_structure(nodes, depth=0):
    structure = {
        'command': [],
        'environment': [],
        'special': [],
        'math': []
    }

    for node in nodes:
        if isinstance(node, LatexMacroNode):
            structure['command'].append({'name': node.macroname, 'depth': depth})
            if node.nodeargd:
                sub_structure = extract_structure(node.nodeargd.argnlist, depth + 1)
                for key in sub_structure:
                    structure[key].extend(sub_structure[key])
        elif isinstance(node, LatexEnvironmentNode):
            structure['environment'].append({'name': node.envname, 'depth': depth})
            sub_structure = extract_structure(node.nodelist, depth + 1)
            for key in sub_structure:
                structure[key].extend(sub_structure[key])
        elif isinstance(node, LatexGroupNode):
            sub_structure = extract_structure(node.nodelist, depth + 1)
            for key in sub_structure:
                structure[key].extend(sub_structure[key])
        elif isinstance(node, LatexSpecialsNode):
            structure['special'].append({'chars': node.specials_chars, 'depth': depth})
        elif isinstance(node, LatexMathNode):
            structure['math'].append({'type': node.displaytype, 'depth': depth})
            sub_structure = extract_structure(node.nodelist, depth + 1)
            for key in sub_structure:
                structure[key].extend(sub_structure[key])

    return structure

def extract_title(latex_code):
    """
    提取 LaTeX 文本中的标题内容（\title{...}）。
    
    Args:
        latex_content (str): LaTeX 文本内容。
    
    Returns:
        str: 提取的标题内容，如果未找到则返回 None。
    """
    # 正则表达式匹配 \title{...}，忽略所有修饰命令
    title_start = latex_code.find(r"\title{")
    if title_start == -1:
        title_start = latex_code.find(r"\title[")
    if title_start == -1:
        return "No title"  
    
    brace_start = latex_code.find("{", title_start)
    if brace_start == -1:
        return "No title"  
    
    stack = []  
    for i in range(brace_start, len(latex_code)):
        if latex_code[i] == "{":
            stack.append(i)  
        elif latex_code[i] == "}":
            stack.pop()  
            if not stack:  
                return latex_code[brace_start + 1:i].strip()

    return "No title"  

def extract_abstract(latex_code):
    """
    提取 LaTeX 文本中的 abstract 环境内容。
    
    Args:
        latex_content (str): LaTeX 文本内容。
    
    Returns:
        str: 提取的 abstract 内容，如果未找到则返回 None。
    """
    # 正则表达式匹配 \begin{abstract} ... \end{abstract}
    abstract_pattern = regex.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", regex.DOTALL)
    
    # 搜索匹配
    match = abstract_pattern.search(latex_code)
    
    # 提取 abstract 内容
    if match:
        abstract = match.group(1).strip() 
        return abstract
    
    abstract_start = latex_code.find(r"\abstract{")
    if abstract_start == -1:
        return "No abstract"

    # 找到第一个花括号的起始位置
    brace_start = latex_code.find("{", abstract_start)
    if brace_start == -1:
        return "No abstract"

    # 使用堆栈提取花括号中的内容
    stack = []
    for i in range(brace_start, len(latex_code)):
        if latex_code[i] == "{":
            stack.append(i)  # 将左花括号的位置压入堆栈
        elif latex_code[i] == "}":
            stack.pop()  # 遇到右花括号，弹出堆栈
            if not stack:  # 堆栈为空，表示匹配完成
                return latex_code[brace_start + 1:i].strip()

    return "No abstract" 

def extract_keywords(latex_code):
    """
    提取 LaTeX 文本中的关键词内容（\keywords{{...}}）或（\keywords{...}）。
    
    Args:
        latex_content (str): LaTeX 文本内容。
    
    Returns:
        str: 提取的关键词内容，如果未找到则返回 None。
    """
    # 正则表达式匹配 \keywords{{...}}
    keywords_pattern = regex.compile(r"\\keywords\{(?:\{([^{}]*)\}|([^{}]*))\}", regex.DOTALL)
    
    # 搜索匹配
    match = keywords_pattern.search(latex_code)
    
    keywords = match.group(1) or match.group(2) if match else None
    # 提取关键词内容
    return keywords.strip() if keywords else None

def extract_sections(latex_code):
    """
    将 LaTeX 文本从第一个 \section 或类似命令处分成前后两部分。
    
    Args:
        latex_code (str): LaTeX 文本内容。
    
    Returns:
        tuple: (before_section, after_section)，分别表示节标题前后的内容。
               如果没有找到节标题，则返回 (latex_code, "")。
    """
    section_pattern = regex.compile(r"\\(section|chapter)\b")
    match = section_pattern.search(latex_code)
    if not match:
        # 如果没有找到节标题，返回原文本和空字符串
        return latex_code, ""
    
    section_index = match.start()
    before_section = latex_code[:section_index]
    after_section = latex_code[section_index:]
    return before_section, after_section

def extract_captions(latex_code):
    """
    从图环境中提取 \caption 命令中最外层花括号的内容（不使用正则表达式）。
    
    Args:
        figure_code (str): 单个图环境的 LaTeX 文本。
    
    Returns:
        str: caption 的内容，如果未找到则返回 "No caption"。
    """
    caption_start = latex_code.find(r"\caption{")
    if caption_start == -1:
        caption_start = latex_code.find(r"\caption[")
    if caption_start == -1:
        return "No caption"  
    
    brace_start = latex_code.find("{", caption_start)
    if brace_start == -1:
        return "No caption"  
    
    stack = []  
    for i in range(brace_start, len(latex_code)):
        if latex_code[i] == "{":
            stack.append(i)  
        elif latex_code[i] == "}":
            stack.pop()  
            if not stack:  
                return latex_code[brace_start + 1:i].strip()

    return "No caption"  

def replace_figures(latex_code):
    """
    将 LaTeX 文本中的图环境替换为占位符 <FIGURE: {caption内容}>。
    
    Args:
        latex_code (str): LaTeX 文本内容。
    
    Returns:
        str: 替换后的 LaTeX 文本。
    """
    figure_pattern = regex.compile(
        r"\\begin\{(figure\*?|wrapfigure|SCfigure|tikzpicture)\}.*?\\end\{\1\}",
        regex.DOTALL
    )
    
    def replace_match(match):
        figure_code = match.group(0)  
        caption = extract_captions(figure_code)  
        return f"<FIGURE: {caption}>"
    
    latex_code = figure_pattern.sub(replace_match, latex_code)
    return latex_code

def replace_tables(latex_code):
    """
    将 LaTeX 文本中的表环境替换为占位符 <TABLE: {caption内容}>。
    
    Args:
        latex_code (str): LaTeX 文本内容。
    
    Returns:
        str: 替换后的 LaTeX 文本。
    """
    table_pattern = regex.compile(
        r"\\begin\{(table\*?|tabular|tabularx|longtable)\}.*?\\end\{\1\}",
        regex.DOTALL
    )
    
    def replace_match(match):
        table_code = match.group(0)  
        caption = extract_captions(table_code)  
        return f"<TABLE: {caption}>"
    
    latex_code = table_pattern.sub(replace_match, latex_code)
    return latex_code

def replace_newcommand(newcommand, latex_code):
    command_name, n_arguments, content = newcommand
    pattern = regex.compile(get_pattern_command_full(command_name, n_arguments), regex.DOTALL)

    def replace_function(match):
        this_content = content
        name = match.group(1)
        assert re.match(command_name, name)
        for i in range(n_arguments):
            text = match.group(3 + i * 2)
            this_content = this_content.replace(f'#{i+1}', f' {text} ')
        return this_content

    return pattern.sub(replace_function, latex_code)

def process_newcommands(latex_code):

    def get_nonNone(*args):
        result = [arg for arg in args if arg is not None]
        assert len(result) == 1
        return result[0]

    pattern_newcommand = rf'\\(?:newcommand\*?|def|renewcommand){spaces}(?:\{{\\([a-zA-Z]+)\}}|\\([a-zA-Z]+)){spaces}(?:\[(\d)\])?{spaces}({get_pattern_brace(4)})'  # \newcommand{name}[n_arguments]{content}, group 1/2: name, group 3: n_arguments, group 5: content

    pattern = regex.compile(pattern_newcommand, regex.DOTALL)
    count = 0
    full_newcommands = []
    match = pattern.search(latex_code)
    while match:
        name1 = match.group(1)
        name2 = match.group(2)
        name = get_nonNone(name1, name2)
        n_arguments = match.group(3)
        if n_arguments is None:
            n_arguments = 0
        else:
            n_arguments = int(n_arguments)
        content = match.group(5)
        latex_code = latex_code.replace(match.group(), f'REPLACE_{count}_NEWCOMMAND')
        # print(latex_code)
        full_newcommands.append(match.group(0))
        latex_code = replace_newcommand((name, n_arguments, content), latex_code)
        count += 1
        match = pattern.search(latex_code)
    for i in range(count):
        latex_code = latex_code.replace(f'REPLACE_{i}_NEWCOMMAND', full_newcommands[i])
    return latex_code

def replace_href(latex_code):
    """
    将 LaTeX 文本中的 \href 命令替换为显示文本部分。
    因为pylatexenc.latex2text处理不了\href命令，所以需要手动处理。
    Args:
        latex_code (str): LaTeX 文本内容。
    
    Returns:
        str: 替换后的 LaTeX 文本。
    """
    # 正则表达式匹配 \href{...}{...}
    href_pattern = regex.compile(r"\\href\{[^{}]*\}\{(.*?)\}")
    
    # 替换 \href 命令为显示文本部分
    latex_code = href_pattern.sub(r"\1", latex_code)
    return latex_code

def replace_includegraphics(latex_code):
    includegraphics_pattern = regex.compile(r"\\includegraphics(?:\[[^\]]*\])?\{[^\}]*\}", regex.DOTALL)
    latex_code = includegraphics_pattern.sub("", latex_code)
    return latex_code

def process_latex_to_eva(latex_code):
    latex_code = replace_href(latex_code)
    latex_code = replace_includegraphics(latex_code)
    latex_code = process_newcommands(latex_code)
    before_section, after_section = extract_sections(latex_code)
    title = extract_title(before_section) if extract_title(before_section) else 'No title'
    abstract = extract_abstract(before_section) if extract_abstract(before_section) else 'No abstract'
    keywords = extract_keywords(before_section) if extract_keywords(before_section) else ''
    after_section = replace_figures(after_section)
    after_section = replace_tables(after_section)
    tex_to_eva = f"{title}\n\n{abstract}\n\n{keywords}\n\n{after_section}"
    return tex_to_eva

def delete_ph(text) -> str:

    pattern = r'§(\.§){0,2}'
    text = re.sub(pattern, '', text)
    placeholder_pattern = r"<.*?PLACEHOLDER.*?>"
    text = re.sub(placeholder_pattern, "", text).strip()
    text = text.replace('\n', ' ')
    
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def extract_pure_text(dir):
    main_file_path = find_main_tex_file(dir)
    if main_file_path is None:
        raise FileNotFoundError(f"File not found: {main_file_path}")
    full_latex_code = merge_tex_from_inputs(main_file_path)
    main_latex_code = process_latex_to_eva(full_latex_code)
    pure_text = extract_text_from_tex(main_latex_code)
    return pure_text

def get_texts_from_data(folder_path, output_folder):
    """
    Extract pure text from all LaTeX files in the given folder and save them as .txt files.
    Display a progress bar while processing projects.
    
    Args:
        folder_path (str): Path to the folder containing projects.
        output_folder (str): Path to the folder where .txt files will be saved.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    extract_compressed_files(folder_path)
    projects = get_profect_dirs(folder_path)
    # print("projects:", projects)
    for project in tqdm(projects, desc="Processing projects", unit="project"):
        try:
            text = extract_pure_text(project)
            project_name = os.path.basename(project)
            output_file = os.path.join(output_folder, f"{project_name}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Error processing project {project}: {e}")
            continue  # 跳过出错的项目

def if_has_appendix(folder_path):
    """
    检测 LaTeX 源码中是否包含 \\appendix。
    
    Args:
        folder_path (str): LaTeX 源码所在文件夹的路径。
    
    Returns:
        bool: 如果包含 \\appendix，则返回 True；否则返回 False。
    """
    projects = get_profect_dirs(folder_path)
    project_app = []
    for project in projects:
        main_file_path = find_main_tex_file(project)
        if main_file_path is None:
            raise FileNotFoundError(f"File not found: {main_file_path}")
        full_latex_code = merge_tex_from_inputs(main_file_path)
        if has_appendix(full_latex_code):
            project_app.append(project)
    return project_app

def extract_pure_tags(dir):
    main_file_path = find_main_tex_file(dir)
    if main_file_path is None:
        raise FileNotFoundError(f"File not found: {main_file_path}")
    main_latex_code = merge_tex_from_inputs(main_file_path)
    nodes = extract_latex_nodes(main_latex_code)
    tag_structure = extract_structure(nodes)
    return tag_structure

def loop_files(dir):
    all_files = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def read_tex_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        latex_code = f.read()
    return latex_code

def read_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data
    
def find_tex_files(dir):
    #找到所有tex文件
    all_files = loop_files(dir)

    tex_files = [f for f in all_files if f.endswith('.tex')]

    return tex_files

def remove_comments(tex: str) -> str:
    """
    Remove both % line comments and \\begin{comment} ... \\end{comment} blocks from LaTeX code.
    """
    # Remove \begin{comment}...\end{comment} environments
    tex = re.sub(r'\\begin\s*\{comment\}.*?\\end\s*\{comment\}', '', tex, flags=re.DOTALL)

    lines = tex.splitlines()
    cleaned = []
    for line in lines:
        stripped_line = line.lstrip()
        # Skip full-line comments (ignoring leading whitespace)
        if re.match(r'^(?<!\\)%', stripped_line):
            continue
        # Remove inline comments (ignore escaped %)
        line = re.sub(r'(?<!\\)%.*', '', line)
        cleaned.append(line.rstrip())  # Optionally remove trailing whitespace

    return '\n'.join(cleaned)

def compress_newlines(tex):
    """
    Replace consecutive newlines (including spaces) exceeding four with exactly two newlines.

    Args:
        content (str): The input string to process.

    Returns:
        str: The processed string with normalized newlines.
    """
    return re.sub(r'(\s*\n\s*){3,}', '\n\n', tex)

def get_env_pattern(command_name):
    """
    Get the regex pattern for matching environments.
    """
    get_command_env = lambda name: rf"\\begin{spaces}\{{(?!document\b|center\b|proof\b|multicols\b)({name})\}}{spaces}({options})?(.*?)\\end{spaces}\{{\1\}}"
    command_env = get_command_env(command_name)
    env_pattern = regex.compile(command_env, regex.DOTALL)
    return env_pattern

def get_abstract_pattern():
    """
    Get the regex pattern for matching \begin{abstract} and \end{abstract} commands.
    """
    command_name = r'abstract'
    get_command_env = lambda name: rf"\\begin{spaces}\{{({name})\}}{spaces}({options})?(.*?)\\end{spaces}\{{\1\}}"
    command_abstract = get_command_env(command_name)
    abstract_pattern = regex.compile(command_abstract, regex.DOTALL)
    return abstract_pattern

def get_keywords_pattern():
    """
    Get the regex pattern for matching \keywords commands.
    """
    command_name = r'keywords'
    command = get_pattern_command_full(command_name)
    keywords_pattern = regex.compile(command, regex.DOTALL)
    return keywords_pattern

def get_section_pattern():
    """
    Get the regex pattern for matching section commands.
    """
    command_name = r'section|subsection|subsubsection' # add chapter
    command = get_pattern_command_full(command_name)
    section_pattern = regex.compile(command, regex.DOTALL)
    return section_pattern

def get_begin_document_pattern():
    """
    Get the regex pattern for matching \begin{document} command.
    """
    pattern = regex.compile(r'\\begin\s*\{\s*document\s*\}', regex.DOTALL)
    return pattern

def get_newcommand_pattern():
    """
    Get the regex pattern for matching \newcommand commands.
    """
    newcommand = rf'\\(?:newcommand\*?|def|renewcommand|newenvironment|renewenvironment){spaces}(?:\{{\\([a-zA-Z]+)\}}|\\([a-zA-Z]+)){spaces}(?:\[(\d)\])?{spaces}({get_pattern_brace(4)})'  # \newcommand{name}[n_arguments]{content}, group 1/2: name, group 3: n_arguments, group 5: content
    newcommand_pattern = regex.compile(newcommand, regex.DOTALL)
    return newcommand_pattern

def get_command_pattern(name):
    """
    Get the regex pattern for matching LaTeX commands.
    """
    command = get_pattern_command_full(name)
    command_pattern = regex.compile(command, regex.DOTALL)
    return command_pattern

def get_captionof_pattern():
    """
    Match \captionof{env}{text} structure using regex with support for nested braces.
    """
    pattern = regex.compile(r"""
        \\captionof          # match \captionof
        \s*                  # optional whitespace
        (?P<braces>          # named group 'braces' to handle nested {}
            \{               # opening {
                (?:          # non-capturing group
                    [^{}]+   # non-brace characters
                    |        # OR
                    (?&braces)  # recursive match for nested braces
                )*
            \}               # closing }
        )
        \s*                  # optional whitespace
        (?P=braces)          # repeat the same structure for the second argument
    """, regex.VERBOSE | regex.DOTALL)
    return pattern

def add_chinese_support_placeholder(latex_code: str) -> str:
    """
    Inserta un marcador de posición para el paquete de chino después de CADA
    comando \\documentclass en el código LaTeX.

    Args:
        latex_code (str): El contenido del archivo LaTeX.

    Returns:
        str: El código LaTeX modificado con los marcadores de posición insertados.
    """
    placeholder = "%%CHINESE_PACKAGE_PLACEHOLDER%%"
    
    # Prevenir la inserción múltiple si la función se llama varias veces
    if placeholder in latex_code:
        return latex_code

    # Patrón para encontrar \documentclass con sus posibles argumentos opcionales y obligatorios
    # Capturamos todo el comando en un grupo para poder referenciarlo en el reemplazo
    documentclass_pattern = r"(\\documentclass(?:\[.*?\])?\{[^}]*\})"
    
    # La cadena de reemplazo: el comando \documentclass original (\1), seguido de
    # un salto de línea, el marcador de posición y otro salto de línea.
    replacement = r"\1\n" + placeholder + "\n"
    
    # re.sub reemplazará todas las ocurrencias que coincidan con el patrón
    modified_code = re.sub(documentclass_pattern, replacement, latex_code)
    
    return modified_code

def add_luatexja_package(latex_code):
    """
    在 LaTeX 文档的 \documentclass 之后添加 luatexja 包，以便支持日文。
    """
    # 检查是否已经包含了 ctex 包
    if "\\usepackage{luatex-ja}" not in latex_code:
        # 使用更可靠的正则表达式来匹配 \documentclass
        documentclass_pattern = re.compile(r'\\documentclass(\[.*?\])?\{.*?\}')
        match = documentclass_pattern.search(latex_code)
        
        if match:
            # 在 \documentclass 命令之后插入 ctex 包
            position = match.end()
            ctex_package = "\\usepackage{luatexja}"
            latex_code = latex_code[:position] + "\n" + ctex_package + "\n" + latex_code[position:]
            
    return latex_code

def find_main_tex_file(directory: str):
    """
    Find the main LaTeX file in the given directory.
    """
    readme_path = os.path.join(directory, '00README.json') 
    if os.path.exists(readme_path):
        config = read_json_file(readme_path)
        for source in config.get("sources", []):
            if source.get("usage") == "toplevel":
                main_file_name = source.get("filename")
                main_file_path = os.path.join(directory, main_file_name)
                return main_file_path if os.path.exists(main_file_path) else None

    tex_files = find_tex_files(directory)
    documentclass_pattern = re.compile(r"\\document(class|style)(\[.*?\])?\{.*?\}", re.DOTALL)
        
    for tex_file in tex_files:

        # Read the LaTeX code
        with open(tex_file, 'r', encoding='utf-8') as f:
            latex_code = f.read()
        latex_code = remove_comments(latex_code)    
        
        # Check if \documentclass is present
        if not documentclass_pattern.search(latex_code):
            continue

        return tex_file
    
    return None

def merge_tex_from_inputs(main_file_path):

    if main_file_path is None:
        return None
    dirname = os.path.dirname(main_file_path)
    maincontent = read_tex_file(main_file_path)
    maincontent = remove_comments(maincontent) 
    pattern_input = re.compile(r'\\(input|include){(.*?)}')
    while True:
        result = pattern_input.search(maincontent)
        if result is None:
            break
        begin, end = result.span()
        match = result.group(2)
        inputfilepath = os.path.join(dirname, match)
        if match.endswith('.tex'): #判断input的文件是否以.tex结尾
            if os.path.exists(f'{inputfilepath}'):
                inputfilepath = f'{inputfilepath}'
            else:
                raise FileNotFoundError(f"File not found: {inputfilepath}")
        else:
            if os.path.exists(f'{inputfilepath}.tex'):
                inputfilepath = f'{inputfilepath}.tex'
            else:
                raise FileNotFoundError(f"File not found: {inputfilepath}.tex")
        input_tex = read_tex_file(inputfilepath)
        input_tex = remove_comments(input_tex)
        maincontent = maincontent[:begin] + input_tex + maincontent[end:]
        # print('merging', inputfilepath)

    return maincontent

def save_to_tex(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(data)

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def compile_with_latexmk(tex_file: str, out_dir: str = "out", engine: str = "pdflatex"):
    os.makedirs(out_dir, exist_ok=True)
    
    cmd = [
        "latexmk",
        f"-{engine}",                # 指定编译引擎，比如 -xelatex
        "-interaction=nonstopmode",   # 不停下来
        f"-outdir={out_dir}",          # 输出目录
        f"-synctex=1",
        f"-f",                 # 强制编译
        tex_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 编译成功！")
    except subprocess.CalledProcessError as e:
        print("❌ 编译失败！")
        print(e)

def collect_latex_errors_with_logpath(folder: str):
    """
    遍历每个项目，优先查找 build_pdflatex 目录，其次是 build 目录，
    读取其中的 .log 文件，统计 LaTeX Error 出现次数。
    仅将包含错误的项目记录到 JSON 文件中，并输出错误项目总数。
    """
    error_keyword = re.compile(r"latex error", re.IGNORECASE)
    summary = {}
    error_project_count = 0

    for project_name in os.listdir(folder):
        project_path = os.path.join(folder, project_name)
        if not os.path.isdir(project_path):
            continue

        preferred_builds = ["build_pdflatex", "build"]
        build_path = None
        for build_dir in preferred_builds:
            candidate = os.path.join(project_path, build_dir)
            if os.path.isdir(candidate):
                build_path = candidate
                break

        if build_path is None:
            continue  # 没有找到 build 目录

        log_files = [f for f in os.listdir(build_path) if f.endswith(".log")]
        if not log_files:
            continue  # 没有 log 文件

        log_path = os.path.join(build_path, log_files[0])
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                error_count = len(error_keyword.findall(content))
        except Exception as e:
            print(f"Error reading {log_path}: {e}")
            continue

        if error_count > 0:
            summary[project_name] = {
                "total_errors": error_count,
                "log_path": log_path
            }
            error_project_count += 1

    # 写入 JSON 文件（仅包含有错误的项目）
    output_path = os.path.join(folder, "latex_error_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Summary saved to: {output_path}")
    print(f"🔍 共有 {error_project_count} 个项目存在 LaTeX Error。")

def get_tex_url(arxiv_id: str, headers: dict) -> str:
    """
    获取 TeX 源码下载链接
    """
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    try:
        resp = requests.get(abs_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return ""
    
    soup = BeautifulSoup(resp.text, "html.parser")
    link = soup.find("a", class_="abs-button download-eprint")
    if link and link.get("href"):
        return f"https://arxiv.org{link['href']}"
    return ""

def is_already_downloaded(arxiv_id: str, save_dir: str) -> bool:
    """
    检查 tar.gz 文件或已解压目录是否存在
    """
    tar_path = os.path.join(save_dir, f"{arxiv_id}.tar.gz")
    extracted_dir = os.path.join(save_dir, arxiv_id)
    return os.path.exists(tar_path) or os.path.isdir(extracted_dir)

def download_tex(arxiv_id: str, tex_url: str, save_dir: str, headers: dict):
    """
    下载 TeX 源码 .tar.gz 文件
    """
    # os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{arxiv_id}.tar.gz")

    try:
        with requests.get(tex_url, headers=headers, stream=True, timeout=20) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("Content-Length", 0))
            with open(file_path, "wb") as f, tqdm(
                desc=f"Download: {arxiv_id}",
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        print(f"[SUCCESS] {arxiv_id} successfully downloaded to {file_path}.")    
        return os.path.join(save_dir, f"{arxiv_id}")

    except requests.RequestException as e:
        print(f"[FAIL] {arxiv_id} download failed: {e}")

def batch_download_arxiv_tex(arxiv_ids: List[str], save_dir: str = "./tex_sources"):
    """
    批量下载多个 arXiv 论文的 TeX 源码
    """
    source_dirs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for arxiv_id in arxiv_ids:
        if is_already_downloaded(arxiv_id, save_dir):
            source_dirs.append(os.path.join(save_dir, arxiv_id))
            print(f"[SkIP] Already downloaded: {arxiv_id}")
            continue

        tex_url = get_tex_url(arxiv_id, headers)
        if tex_url:
            dir = download_tex(arxiv_id, tex_url, save_dir, headers)
            source_dirs.append(dir)
        else:
            print(f"[SKIP] No TeX source found for {arxiv_id}. Please check the arXiv ID or the availability of the source.")

    return source_dirs

def select_tex_distribution(distributions: Dict[str, str]) -> str:
    """Prompts the user to select a LaTeX distribution and returns the path to latexmk."""
    print("\nPlease choose which one to use:")
    
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

def detect_tex_distributions():
    """
    Detects available LaTeX distributions (TeX Live and MiKTeX) on a Windows system.
    Returns:
        A dictionary mapping the distribution name to the full path of its latexmk executable.
    """
    distributions = {}
    if platform.system() != "Windows":
        # Check for latexmk in PATH on non-Windows systems
        path = shutil.which("latexmk")
        if path:
            # Simple check, can be improved to differentiate linux distros
            distributions["Default"] = path
        return distributions

    try:
        # On Windows, 'where' command can find all executables in PATH.
        # CREATE_NO_WINDOW is only available on Windows
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'latexmk.exe'], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            result = subprocess.run(['which', 'latexmk'], capture_output=True, text=True, check=True)
        paths = result.stdout.strip().split('\n')
        
        for path in paths:
            path = path.strip()
            if not path:
                continue
            
            lower_path = path.lower()
            # Identify distribution by common path components
            if 'texlive' in lower_path:
                distributions['TeX Live'] = path
            elif 'miktex' in lower_path:
                distributions['MiKTeX'] = path
            else:
                # Fallback for unusually named paths
                if 'TeX Live' not in distributions and 'MiKTeX' not in distributions:
                     distributions['Unknown'] = path

    except (subprocess.CalledProcessError, FileNotFoundError):
        # 'where' command not found or returned an error (e.g., no latexmk.exe found)
        pass
        
    return distributions


# get_texts_from_data(
#     folder_path="D:\code\AutoLaTexTrans\data\cs",
#     output_folder="D:\code\AutoLaTexTrans\cs_puretext"
# )

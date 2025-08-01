from typing import Any, Dict, Optional
from .utils import *
import tiktoken
import sys

import streamlit as st


class LatexParser:
    def __init__(self, dir: str, output_dir: str):
        self.inputs_json = []
        self.envs_json = []
        self.captions_json = []
        self.newcommands_json = []
        self.sections_json = []
        self.dir = dir # LaTex profect directory
        self.output_dir = output_dir # Output directory for parsed files
        self.env_count = 0
        self.caption_count = 0

    def parse(self):
        """
        Parse the LaTeX document and return the parsed content.
        """
        sys.stderr = open(os.devnull, 'w')
        process_b = st.empty()
        with process_b:
            process_bar = st.progress(0, text="Parsing LaTeX document...")
        sys.stderr = sys.__stderr__

        main_tex_file = find_main_tex_file(self.dir) 
        if not main_tex_file:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None

        sys.stderr = open(os.devnull, 'w')
        process_bar.progress(10, text="Finding main tex file...")
        sys.stderr = sys.__stderr__

        main_tex = read_tex_file(main_tex_file)
        if not main_tex:
            print("⚠️ Warning: The main tex file is empty.")
            return None
        
        sys.stderr = open(os.devnull, 'w')
        process_bar.progress(20,text="Reading main tex file...")
        sys.stderr = sys.__stderr__

        main_tex = remove_comments(main_tex)
        full_tex = self._merge_inputs(main_tex)
        full_tex = self._extract_newcommands(full_tex)
        # full_tex = compress_newlines(full_tex)
        self._split_to_sections(full_tex)
        
        # 先处理长章节
        self._split_long_sections(max_tokens=2000)
        # 再合并短章节
        self._merge_short_sections(min_tokens=50)  # Merge short sections to avoid too many sections

        total_sections = len(self.sections_json)
        sys.stderr = open(os.devnull, 'w')
        process_bar.progress(80)
        sys.stderr = sys.__stderr__

        for i,section in enumerate(self.sections_json):

            sys.stderr = open(os.devnull, 'w')
            process_text = f"Processing chapter：{i+1}/{total_sections}"
            process_bar.progress(80 + int(15 * (i/total_sections)), text=process_text)
            sys.stderr = sys.__stderr__

            if section["section"] == "0" or section["section"] == "-1":
                section_content = self._extract_captions(section["content"])
                self.sections_json[i]["trans_content"] = self._extract_envs(section_content)
                self.sections_json[i]["content"] = self.sections_json[i]["trans_content"]
            else:
                section_content = self._extract_captions(section["content"])
                self.sections_json[i]["content"] = self._extract_envs(section_content)

        sys.stderr = open(os.devnull, 'w')
        process_bar.progress(100, text="Finish Parse Sections")
        st.success("Finish Parse Sections")
        process_b.empty()
        sys.stderr = sys.__stderr__

    def parse_no_env_cap_ph(self):
        """
        Parse the LaTeX document and return the parsed content.
        """
        main_tex_file = find_main_tex_file(self.dir) 
        if not main_tex_file:
            print("⚠️ Warning: There is no main tex file to compile in this directory.")
            return None
        main_tex = read_tex_file(main_tex_file)
        if not main_tex:
            print("⚠️ Warning: The main tex file is empty.")
            return None
        
        main_tex = remove_comments(main_tex)
        full_tex = self._merge_inputs(main_tex)
        full_tex = self._extract_newcommands(full_tex)
        full_tex = compress_newlines(full_tex)
        self._split_to_sections(full_tex)
        self._merge_short_sections(min_tokens=20)  # Merge short sections to avoid too many sections

    def _merge_inputs(self, tex: str) -> str:
        """
        Merge all the inputs in the main tex file and genarate a json file for the inputs.
        """
        main_tex = remove_comments(tex) 
        command_name = r'input|include'
        pattern_input = get_command_pattern(command_name) # \input{file.tex} or \input{file} or \include{file.tex} or \include{file}
        pos = 0
        while True:
            result = pattern_input.search(main_tex, pos)
            if result is None:
                break
            begin, end = result.span()
            pos = result.end()
            match = result.group(4)
            inputfilepath = os.path.join(self.dir, match)

            if os.path.exists(f'{inputfilepath}'):
                inputfilepath = f'{inputfilepath}'
            elif os.path.exists(f'{inputfilepath}.tex'):
                inputfilepath = f'{inputfilepath}.tex'
            else:
                print(f"⚠️ Warning: File not found: {inputfilepath}.tex or {inputfilepath}")
                pos = result.end()  # Skip this input and continue
                continue

            input_tex = read_tex_file(inputfilepath)
            input_tex = remove_comments(input_tex)
            input_begin = f"<PLACEHOLDER_{match}_begin>"
            input_end = f"<PLACEHOLDER_{match}_end>"
            input_tex = input_begin + input_tex + input_end
            main_tex = main_tex[:begin] + input_tex + main_tex[end:]
            self.inputs_json.append({
                "command": result.group(0),
                "begin": input_begin,
                "end": input_end,
                "path": match
            })

        return main_tex

    def _extract_envs(self, tex: str) -> str:
        """
        Extract all the environments in the full tex and generate a json file for the environments.
        The environments are replaced with placeholders in the full tex.
        """
        full_tex = remove_comments(tex)
        command_name = r'.*?'
        pattern_env = get_env_pattern(command_name) # \begin{env}...\end{env} or \begin{env}...\end{env}* or \begin{env}[options]...\end{env}
        placeholder_pattern_cap= r"<PLACEHOLDER_CAP_\d+>"
        no_translate_envs = [
                             'equation', 'align', 'align*', 'gather', 'gather*', 'verbatim', 'verbatim*', 'lstlisting*', 'minted', 'minted*',
                             'equation*', 'alignat', 'alignat*', 'flalign', 'flalign*', 'split', 'split*', 'cases', 'cases*', 'subequations', 
                             'figure', 'figure*', 'wrapfigure', 'SCfigure', 'tikzpicture', 'CJK', 'scope',
                             'tabularx', 'tabulary', 'longtable*', 'sidewaystable', 'table', 'table*', 'tabular', 'tabular*', 'longtable',
                             'multline', 'multline*', 'lstlisting', 'tcolorbox', 'thebibliography', 'bibliography', 'bibitem',
                             'algorithm', 'algorithmic', 'algorithmicx', 'algorithm2e', 'algorithmicx*', 'algorithmic*', 'algorithm*'
                             ]
        while True:
            result = pattern_env.search(full_tex)
            if result is None:
                break
            self.env_count += 1
            env_name = result.group(1)
            env_content = result.group(0)
            placeholders_cap_in_env = re.findall(placeholder_pattern_cap, env_content)

            need_trans = True

            if env_name in no_translate_envs:
                need_trans = False

            if placeholders_cap_in_env:
                # If there are placeholders in the environment, we do not translate it.
                need_trans = False

            placeholder = f"<PLACEHOLDER_ENV_{self.env_count}>"
            full_tex = full_tex.replace(env_content, placeholder, 1)
            self.envs_json.append({
                "placeholder": placeholder,
                "env_name": env_name,
                "content": env_content,
                "trans_content": '',
                "need_trans": need_trans
            })
        
        return full_tex

    def _extract_captions(self, tex: str) -> str:
        """
        Extract all the captions in the full tex and genarate a json file for the captions.
        The captions are replaced with placeholders in the full tex.
        """
        full_tex = remove_comments(tex)
        command_name = r'caption|caption\*|subcaption|subcaption\*|title|keywords|abstract|icmltitle|icmltitlerunning'
        pattern_caption = get_command_pattern(command_name) # \caption{...} or \caption*{...} or \caption[...]{...}
        # pattern_captionof = get_captionof_pattern() # \captionof{type}{content} or \captionof*{type}{content}

        while True:
            result = pattern_caption.search(full_tex)
            if result is None:
                break
            self.caption_count += 1
            placeholder = f"<PLACEHOLDER_CAP_{self.caption_count}>"
            full_tex = full_tex.replace(result.group(0), placeholder, 1)
            self.captions_json.append({
                "placeholder": placeholder,
                "cap_type":result.group(1),
                "content": result.group(0),
                "trans_content": ''
            })

        return full_tex
    
    def _extract_newcommands(self, tex: str) -> str:
        """
        Extract all the newcommands in the full tex and genarate a json file for the newcommands.
        """
        def get_nonNone(*args):
            result = [arg for arg in args if arg is not None]
            assert len(result) == 1
            return result[0]
        
        full_tex = remove_comments(tex)
        pattern = get_newcommand_pattern() # \newcommand{name}[n_arguments]{content} or \renewcommand{name}[n_arguments]{content} or \newenvironment{name}[n_arguments]{content} or \renewenvironment{name}[n_arguments]{content}
        count = 0
        
        while True:
            match = pattern.search(full_tex)
            if match is None:
                break
            name1 = match.group(1)
            name2 = match.group(2)
            name = get_nonNone(name1, name2)
            n_arguments = match.group(3)
            if n_arguments is None:
                n_arguments = 0
            else:
                n_arguments = int(n_arguments)
            placeholder = f"<PLACEHOLDER_NEWCOMMAND_{count}>"
            full_tex = full_tex.replace(match.group(0), placeholder, 1)
            self.newcommands_json.append({
                "placeholder": placeholder,
                "name": name,
                "content": match.group(0)
            })
            count += 1

        return full_tex
    
    def _split_to_sections(self, tex: str) -> Any:
        """
        Split the full tex to sections and genarate a json file for the sections.
        """
        full_tex = remove_comments(tex)
        command_name_section = r'section|subsection|subsubsection|section\*|subsection\*|subsubsection\*|chapter|chapter\*'
        pattern_section = get_command_pattern(command_name_section) # \section{...} or \subsection{...} or \subsubsection{...}
        begin_document_pattern = get_begin_document_pattern() # \begin{document}
        begin_document_match = begin_document_pattern.search(full_tex)
        preamble = full_tex[:begin_document_match.start()] if begin_document_match else full_tex #...\begin{document}

        self.sections_json.append({
            "section": "-1",
            "content": preamble,
            "trans_content": preamble
        })

        document = full_tex[begin_document_match.start():] if begin_document_match else full_tex

        section_count = 0
        subsection_count = 0
        subsubsection_count = 0
        first_section_match = pattern_section.search(document)

        if not first_section_match: # no section found
            print("There is no section in the full tex.")
            self.sections_json.append({
                "section": "0",
                "content": document,
                "trans_content": ''
            })
            return

        before_section = document[:first_section_match.start()] if first_section_match else document # \begin{document}...\section{...}
        sections_tex = document[first_section_match.start():] if first_section_match else document
        
        self.sections_json.append({
            "section": "0",
            "content": before_section,
            "trans_content": before_section
        })

        last_pos = 0
        last_result = first_section_match

        for result in pattern_section.finditer(sections_tex):
            if last_pos != result.start():
                if last_result.group(1) == "section" or last_result.group(1) == "section*":
                    section_count += 1
                    subsection_count = 0
                    subsubsection_count = 0
                    self.sections_json.append({
                        "section": f'{section_count}',
                        "content": sections_tex[last_pos:result.start()],
                        "trans_content": ''
                    })
                elif last_result.group(1) == "subsection" or last_result.group(1) == "subsection*":
                    subsection_count += 1
                    subsubsection_count = 0
                    self.sections_json.append({
                        "section": f"{section_count}.{subsection_count}",
                        "content": sections_tex[last_pos:result.start()],
                        "trans_content": ""
                    })
                elif last_result.group(1) == "subsubsection" or last_result.group(1) == "subsubsection*":
                    subsubsection_count += 1
                    self.sections_json.append({
                        "section": f"{section_count}.{subsection_count}.{subsubsection_count}",
                        "content": sections_tex[last_pos:result.start()],
                        "trans_content": ""
                    })
            last_pos = result.start()
            last_result = result

        # 处理文档最后一个章节
        if last_result.group(1) == "section" or last_result.group(1) == "section*":
            section_count += 1
            subsection_count = 0
            subsubsection_count = 0
            self.sections_json.append({
                "section": f"{section_count}",
                "content": sections_tex[last_pos:],
                "trans_content": ""
            })
        elif last_result.group(1) == "subsection" or last_result.group(1) == "subsection*":
            subsection_count += 1
            subsubsection_count = 0
            self.sections_json.append({
                "section": f"{section_count}.{subsection_count}",
                "content": sections_tex[last_pos:],
                "trans_content": ""
            })
        elif last_result.group(1) == "subsubsection" or last_result.group(1) == "subsubsection*":
            subsubsection_count += 1
            self.sections_json.append({
                "section": f"{section_count}.{subsection_count}.{subsubsection_count}",
                "content": sections_tex[last_pos:],
                "trans_content": ""
            })

    def _merge_short_sections(self, min_tokens=20):
        enc = tiktoken.encoding_for_model("gpt-4")
        merged_sections = []
        i = 0
        sections = self.sections_json

        while i < len(sections):
            # 初始化当前 section
            combined_content = sections[i]["content"]
            combined_section_ids = [sections[i]["section"]]
            total_tokens = len(enc.encode(combined_content))
            start_section = sections[i]
            j = i + 1

            # 向后合并，直到达到 min_tokens 或结束
            while total_tokens < min_tokens and j < len(sections):
                combined_content += "\n" + sections[j]["content"]
                combined_section_ids.append(sections[j]["section"])
                total_tokens = len(enc.encode(combined_content))
                j += 1

            # 合并成一个新的 section 数据
            if total_tokens < min_tokens and len(merged_sections) > 0:
                # 太短，合并进前一段
                merged_sections[-1]["content"] += "\n" + combined_content
                merged_sections[-1]["section"] += "+" + "+".join(combined_section_ids)
                print(merged_sections[-1]["section"])
            else:
                # 新段落，保留结构并更新字段
                merged_section = start_section.copy()
                merged_section["content"] = combined_content
                merged_section["section"] = "+".join(combined_section_ids)
                merged_sections.append(merged_section)

            i = j

        self.sections_json = merged_sections

    def _split_long_sections(self, max_tokens=1000):
        """
        将过长的章节分割成多个小节，确保：
        1. 不会切断句子
        2. 不会切断LaTeX环境
        3. 尽可能多分割以适应token限制
        Args:
            max_tokens (int): 每个章节的最大token数，默认设置更小以获得更多分段
        """
        enc = tiktoken.encoding_for_model("gpt-4")
        split_sections = []
        
        for section in self.sections_json:
            content = section["content"]
            tokens = len(enc.encode(content))
            
            if tokens > max_tokens:
                # 1. 首先按LaTeX环境分割
                env_pattern = r'\\begin\{.*?\}.*?\\end\{.*?\}'
                parts = re.split(f'({env_pattern})', content)
                
                current_content = ""
                current_tokens = 0
                sub_section_count = 1
                buffer = ""  # 用于临时存储未处理完的内容
                
                for part in parts:
                    # 如果是LaTeX环境，作为一个整体处理
                    if re.match(env_pattern, part):
                        part_tokens = len(enc.encode(part))
                        if current_content and current_tokens + part_tokens > max_tokens:
                            # 保存当前累积的内容
                            split_sections.append({
                                "section": f"{section['section']}.{sub_section_count}",
                                "content": current_content.strip(),
                                "trans_content": ""
                            })
                            sub_section_count += 1
                            current_content = part
                            current_tokens = part_tokens
                        else:
                            if current_content:
                                current_content += "\n\n" + part
                            else:
                                current_content = part
                            current_tokens += part_tokens
                        continue

                    # 2. 对非环境内容，按句子分割
                    sentences = re.split(r'([。！？\n\n])', part)
                    
                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i+1]  # 加上分隔符
                        
                        if not sentence.strip():
                            continue
                            
                        sentence_tokens = len(enc.encode(buffer + sentence))
                        
                        if current_tokens + sentence_tokens > max_tokens and current_content:
                            # 保存当前累积的内容
                            split_sections.append({
                                "section": f"{section['section']}.{sub_section_count}",
                                "content": current_content.strip(),
                                "trans_content": ""
                            })
                            sub_section_count += 1
                            current_content = buffer + sentence
                            current_tokens = len(enc.encode(current_content))
                            buffer = ""
                        else:
                            if current_content:
                                current_content += buffer + sentence
                            else:
                                current_content = buffer + sentence
                            current_tokens += sentence_tokens
                            buffer = ""
                
                # 处理最后剩余的内容
                if buffer:
                    current_content += buffer
                if current_content:
                    split_sections.append({
                        "section": f"{section['section']}.{sub_section_count}",
                        "content": current_content.strip(),
                        "trans_content": ""
                    })
            else:
                # 章节不需要分割，直接添加
                split_sections.append(section)
        
        self.sections_json = split_sections



import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF

logger = logging.getLogger("omnimath.parsing")

# Initialize Tree-Sitter parsers for supported languages (lazy loading)
_PARSERS: Dict[str, Any] = {}

def get_parser(language: str):
    """
    Lazy-loads and caches Tree-Sitter parsers.
    """
    global _PARSERS
    if language in _PARSERS:
        return _PARSERS[language]

    try:
        import tree_sitter
        if language == "python":
            import tree_sitter_python
            py_lang = tree_sitter.Language(tree_sitter_python.language())
            parser = tree_sitter.Parser(py_lang)
            _PARSERS["python"] = parser
            return parser
        elif language in ["javascript", "js", "typescript", "ts"]:
            import tree_sitter_javascript
            js_lang = tree_sitter.Language(tree_sitter_javascript.language())
            parser = tree_sitter.Parser(js_lang)
            _PARSERS["javascript"] = parser
            return parser
    except Exception as e:
        logger.warning(f"Failed to initialize tree-sitter parser for {language}: {e}")
    return None


class ParsingService:
    def __init__(self):
        # Pre-warm parsers for better performance
        get_parser("python")
        get_parser("javascript")

    def infer_topic(self, text: str, name: Optional[str] = None, source: str = "") -> str:
        """
        Infers the programming topic based on keywords, AST name, and file context.
        Also works for mathematical topics.
        """
        combined = f"{source} {name or ''} {text[:300]}".lower()

        # Programming topic keywords
        programming_topic_keywords = {
            "decorators": ["decorator", "@", "wraps", "wrapper"],
            "async_concurrency": ["async", "await", "asyncio", "coroutine", "thread", "promise"],
            "generators_iterators": ["yield", "generator", "iterator", "__iter__", "__next__"],
            "oop_classes": ["class ", "inheritance", "polymorphism", "dunder", "__init__", "metaclass"],
            "context_managers": ["__enter__", "__exit__", "contextmanager", "with "],
            "functional_programming": ["lambda", "map", "filter", "reduce", "closure", "partial"],
            "error_handling": ["try", "except", "finally", "catch", "raise", "exception"],
            "data_structures": ["dict", "set", "tuple", "list comprehension", "heapq", "collections"],
            "algorithms": ["sort", "search", "binary search", "recursion", "dynamic programming", "tree", "graph"],
            "web_apis": ["fastapi", "flask", "router", "endpoint", "request", "response", "get", "post"],
        }

        # Mathematical topic keywords
        math_topic_keywords = {
            "calculus": ["derivative", "integral", "limit", "differentiation", "integration"],
            "algebra": ["equation", "polynomial", "factor", "quadratic", "linear"],
            "statistics": ["mean", "median", "standard deviation", "variance", "probability"],
            "geometry": ["area", "volume", "triangle", "circle", "pythagorean"],
            "trigonometry": ["sine", "cosine", "tangent", "sin", "cos", "tan"],
        }

        # Check programming topics first
        for topic, keywords in programming_topic_keywords.items():
            if any(kw in combined for kw in keywords):
                return topic

        # Check math topics
        for topic, keywords in math_topic_keywords.items():
            if any(kw in combined for kw in keywords):
                return topic

        return "general"

    def infer_difficulty(self, code_or_text: str) -> str:
        """
        Estimates concept difficulty based on structural complexity.
        Works for both code and mathematical text.
        """
        lowered = code_or_text.lower()
        advanced_markers = [
            "metaclass", "asyncio.gather", "bytecode", "custom decorator with arguments",
            "__getattribute__", "weakref", "descriptor", "memoryview", "cython", "ctypes",
            "partial differential equation", "fourier transform", "laplace transform",
            "group theory", "topology", "complex analysis"
        ]
        intermediate_markers = [
            "@classmethod", "@staticmethod", "@property", "yield from", "args", "kwargs",
            "contextmanager", "abstractmethod", "dataclass", "generic", "typing.Union",
            "integration by parts", "chain rule", "implicit differentiation",
            "eigenvalue", "determinant", "matrix multiplication"
        ]

        if any(marker in lowered for marker in advanced_markers):
            return "advanced"
        if any(marker in lowered for marker in intermediate_markers) or len(code_or_text) > 450:
            return "intermediate"
        return "beginner"

    def extract_docstring_from_node(self, node: Any, code_bytes: bytes) -> Optional[str]:
        """
        Extracts docstrings from a Tree-Sitter function or class node.
        """
        body_node = node.child_by_field_name("body")
        if not body_node:
            return None
        for child in body_node.children:
            if child.type == "expression_statement":
                for expr_child in child.children:
                    if expr_child.type == "string":
                        doc_text = code_bytes[expr_child.start_byte:expr_child.end_byte].decode("utf-8", errors="replace")
                        # Strip outer quotes
                        return doc_text.strip("'''\"\"\" \n\t")
            elif child.type != "comment":
                # First non-comment statement was not a string expression
                break
        return None

    def chunk_python_code(self, source_code: str, source_name: str = "snippet.py") -> List[Dict[str, Any]]:
        """
        Parses Python code using Tree-Sitter AST and returns atomic chunks
        for functions, decorated definitions, and classes without breaking code mid-scope.
        """
        parser = get_parser("python")
        if not parser:
            return self._fallback_line_chunk(source_code, "python", source_name)

        code_bytes = source_code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root = tree.root_node

        chunks: List[Dict[str, Any]] = []
        preamble_statements: List[str] = []

        for node in root.children:
            # Handle functions and decorated functions
            is_function = node.type == "function_definition"
            is_decorated = node.type == "decorated_definition"
            is_class = node.type == "class_definition"

            if is_function or is_decorated or is_class:
                node_code = code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()

                # Identify function/class name
                name = None
                sub_type = node.type
                docstring = None

                if is_decorated:
                    def_child = node.child_by_field_name("definition")
                    if def_child:
                        sub_type = f"decorated_{def_child.type}"
                        name_node = def_child.child_by_field_name("name")
                        if name_node:
                            name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace")
                        docstring = self.extract_docstring_from_node(def_child, code_bytes)
                else:
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace")
                    docstring = self.extract_docstring_from_node(node, code_bytes)

                topic = self.infer_topic(node_code, name=name, source=source_name)
                difficulty = self.infer_difficulty(node_code)

                metadata = {
                    "source": source_name,
                    "language": "python",
                    "type": "code_example",
                    "sub_type": sub_type,
                    "name": name or "anonymous",
                    "topic": topic,
                    "difficulty": difficulty,
                    "start_line": node.start_point.row + 1,
                    "end_line": node.end_point.row + 1,
                    "char_count": len(node_code)
                }
                if docstring:
                    metadata["docstring"] = docstring

                chunks.append({
                    "content": node_code,
                    "metadata": metadata
                })
            elif node.type in ["import_statement", "import_from_statement", "expression_statement", "assignment"]:
                stmt_text = code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()
                if stmt_text:
                    preamble_statements.append(stmt_text)

        # If there are top-level script statements without functions/classes, group them
        if preamble_statements and not chunks:
            full_script = "\n".join(preamble_statements)
            chunks.append({
                "content": full_script,
                "metadata": {
                    "source": source_name,
                    "language": "python",
                    "type": "code_example",
                    "sub_type": "script",
                    "name": "module_root",
                    "topic": self.infer_topic(full_script, source=source_name),
                    "difficulty": self.infer_difficulty(full_script),
                    "start_line": 1,
                    "end_line": len(preamble_statements),
                    "char_count": len(full_script)
                }
            })

        logger.info(f"Tree-Sitter parsed {source_name}: generated {len(chunks)} code chunks.")
        return chunks

    def chunk_javascript_code(self, source_code: str, source_name: str = "snippet.js") -> List[Dict[str, Any]]:
        """
        Parses JavaScript/TypeScript code using Tree-Sitter AST and returns atomic chunks
        for functions, classes, and exported declarations.
        """
        parser = get_parser("javascript")
        if not parser:
            return self._fallback_line_chunk(source_code, "javascript", source_name)

        code_bytes = source_code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root = tree.root_node

        chunks: List[Dict[str, Any]] = []

        for node in root.children:
            target_types = ["function_declaration", "class_declaration", "export_statement", "lexical_declaration"]
            if node.type in target_types:
                node_code = code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()
                name_node = node.child_by_field_name("name")
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace") if name_node else None

                chunks.append({
                    "content": node_code,
                    "metadata": {
                        "source": source_name,
                        "language": "javascript",
                        "type": "code_example",
                        "sub_type": node.type,
                        "name": name or "export_or_declaration",
                        "topic": self.infer_topic(node_code, name=name, source=source_name),
                        "difficulty": self.infer_difficulty(node_code),
                        "start_line": node.start_point.row + 1,
                        "end_line": node.end_point.row + 1,
                        "char_count": len(node_code)
                    }
                })

        if not chunks and source_code.strip():
            return self._fallback_line_chunk(source_code, "javascript", source_name)

        return chunks

    def chunk_markdown(self, markdown_text: str, source_name: str = "doc.md") -> List[Dict[str, Any]]:
        """
        Parses Markdown documentation into:
        1. Atomic code blocks tagged with language and type='code_example'.
        2. Focused explanatory sections (800-1200 chars) tagged with type='explanation'.
        Preserves code indentation, headings, and contextual flow.
        Works for both mathematical and programming markdown.
        """
        chunks: List[Dict[str, Any]] = []
        lines = markdown_text.splitlines()

        current_heading = "General Overview"
        prose_buffer: List[str] = []
        code_buffer: List[str] = []
        in_code_block = False
        code_lang = "python"
        code_start_line = 1

        def flush_prose(heading: str, line_no: int):
            nonlocal prose_buffer
            if not prose_buffer:
                return
            full_text = "\n".join(prose_buffer).strip()
            prose_buffer = []
            if not full_text:
                return

            # Split larger explanatory text into 800-1200 char chunks along paragraphs
            paragraphs = full_text.split("\n\n")
            current_chunk = ""
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                if len(current_chunk) + len(p) + 2 <= 1200:
                    current_chunk = f"{current_chunk}\n\n{p}" if current_chunk else p
                else:
                    if current_chunk:
                        chunks.append({
                            "content": current_chunk,
                            "metadata": {
                                "source": source_name,
                                "language": "markdown",
                                "type": "explanation",
                                "topic": self.infer_topic(current_chunk, source=f"{source_name} - {heading}"),
                                "difficulty": self.infer_difficulty(current_chunk),
                                "heading": heading,
                                "char_count": len(current_chunk)
                            }
                        })
                    current_chunk = p
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "metadata": {
                        "source": source_name,
                        "language": "markdown",
                        "type": "explanation",
                        "topic": self.infer_topic(current_chunk, source=f"{source_name} - {heading}"),
                        "difficulty": self.infer_difficulty(current_chunk),
                        "heading": heading,
                        "char_count": len(current_chunk)
                    }
                })

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Heading detection
            if stripped.startswith("#") and not in_code_block:
                flush_prose(current_heading, idx)
                current_heading = stripped.lstrip("#").strip()
                continue

            # Fenced code block detection
            if stripped.startswith("```"):
                if not in_code_block:
                    flush_prose(current_heading, idx)
                    in_code_block = True
                    code_start_line = idx
                    lang_tag = stripped.lstrip("`").strip().lower()
                    code_lang = lang_tag if lang_tag else "python"
                    code_buffer = []
                else:
                    # Closing code fence
                    in_code_block = False
                    code_content = "\n".join(code_buffer)
                    code_buffer = []
                    if code_content.strip():
                        # If Python, we can check if it contains multiple functions
                        if code_lang in ["python", "py"]:
                            ast_chunks = self.chunk_python_code(code_content, f"{source_name}:{current_heading}")
                            if ast_chunks and len(ast_chunks) > 1:
                                chunks.extend(ast_chunks)
                            else:
                                chunks.append({
                                    "content": code_content,
                                    "metadata": {
                                        "source": source_name,
                                        "language": "python",
                                        "type": "code_example",
                                        "heading": current_heading,
                                        "topic": self.infer_topic(code_content, source=f"{source_name} - {current_heading}"),
                                        "difficulty": self.infer_difficulty(code_content),
                                        "start_line": code_start_line,
                                        "end_line": idx,
                                        "char_count": len(code_content)
                                    }
                                })
                        else:
                            chunks.append({
                                "content": code_content,
                                "metadata": {
                                    "source": source_name,
                                    "language": code_lang,
                                    "type": "code_example",
                                    "heading": current_heading,
                                    "topic": self.infer_topic(code_content, source=f"{source_name} - {current_heading}"),
                                    "difficulty": self.infer_difficulty(code_content),
                                    "start_line": code_start_line,
                                    "end_line": idx,
                                    "char_count": len(code_content)
                                }
                            })
                continue

            if in_code_block:
                code_buffer.append(line)
            else:
                prose_buffer.append(line)

        flush_prose(current_heading, len(lines))
        logger.info(f"Parsed Markdown {source_name}: generated {len(chunks)} chunks.")
        return chunks

    def extract_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts structured text and code blocks from PDF documentation.
        Enhanced to detect code blocks in mathematical and programming PDFs.
        """
        try:
            doc = fitz.open(str(pdf_path))
            chunks = []
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                if not text.strip():
                    continue

                # Separate code-like segments (indented or with def/class/import or math notation)
                lines = text.splitlines()
                current_block: List[str] = []
                is_code = False

                for line in lines:
                    line_is_code = line.startswith("    ") or line.startswith("\t") or any(
                        line.strip().startswith(kw) for kw in [
                            "def ", "class ", "import ", "from ", "function ", "const ", "let ",
                            "\\begin{", "\\end{", "$$", "$", "\\int", "\\frac", "\\sum"  # Math notation
                        ]
                    )
                    if line_is_code != is_code and current_block:
                        content = "\n".join(current_block).strip()
                        if content:
                            chunks.append({
                                "content": content,
                                "metadata": {
                                    "source": pdf_path.name,
                                    "page": page_num + 1,
                                    "language": "python" if is_code and not any(math_kw in content.lower() for math_kw in ["\\begin{", "\\int", "\\frac"]) else "text",
                                    "type": "code_example" if is_code else "explanation",
                                    "topic": self.infer_topic(content, source=pdf_path.name),
                                    "difficulty": self.infer_difficulty(content)
                                }
                            })
                        current_block = [line]
                        is_code = line_is_code
                    else:
                        current_block.append(line)

                if current_block:
                    content = "\n".join(current_block).strip()
                    if content:
                        chunks.append({
                            "content": content,
                            "metadata": {
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "language": "python" if is_code and not any(math_kw in content.lower() for math_kw in ["\\begin{", "\\int", "\\frac"]) else "text",
                                "type": "code_example" if is_code else "explanation",
                                "topic": self.infer_topic(content, source=pdf_path.name),
                                "difficulty": self.infer_difficulty(content)
                            }
                        })
            doc.close()
            return chunks
        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            return []

    def _fallback_line_chunk(self, text: str, language: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Fallback chunker if AST parsers are unavailable.
        Works for both code and text.
        """
        chunks = []
        lines = text.splitlines()
        batch_size = 25
        for i in range(0, len(lines), batch_size):
            slice_lines = lines[i:i + batch_size]
            content = "\n".join(slice_lines).strip()
            if content:
                chunks.append({
                    "content": content,
                    "metadata": {
                        "source": source_name,
                        "language": language,
                        "type": "code_example" if language in ["python", "javascript", "text"] else "text_chunk",
                        "topic": self.infer_topic(content, source=source_name),
                        "difficulty": self.infer_difficulty(content),
                        "start_line": i + 1,
                        "end_line": i + len(slice_lines)
                    }
                })
        return chunks

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Universal file parser dispatcher based on extension.
        Routes to appropriate handler based on file type and content.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext == ".py":
            return self.chunk_python_code(file_path.read_text(encoding="utf-8", errors="replace"), file_path.name)
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return self.chunk_javascript_code(file_path.read_text(encoding="utf-8", errors="replace"), file_path.name)
        elif ext in [".md", ".markdown"]:
            return self.chunk_markdown(file_path.read_text(encoding="utf-8", errors="replace"), file_path.name)
        elif ext == ".pdf":
            return self.extract_from_pdf(file_path)
        elif ext in [".txt", ".rst"]:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            return self.chunk_markdown(text, file_path.name)
        else:
            logger.warning(f"Unsupported extension {ext} for {file_path}. Using fallback.")
            text = file_path.read_text(encoding="utf-8", errors="replace")
            return self._fallback_line_chunk(text, "text", file_path.name)

parsing_service = ParsingService()
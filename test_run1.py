from services.parsing_service_code import parsing_service

# Test Python code
chunks = parsing_service.chunk_python_code('def f(): pass', 'test.py')
print(f'Python chunks: {len(chunks)}')

# Test markdown with code
md_string = """# Test

```python
print("hello")
```"""

md_chunks = parsing_service.chunk_markdown(md_string, 'test.md')
print(f'Markdown chunks: {len(md_chunks)}')
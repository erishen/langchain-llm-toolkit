import unittest
import os
import tempfile
from unittest.mock import patch
from langchain_llm_toolkit.document_loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DocumentLoader()
        # 创建临时测试文件
        self.temp_dir = tempfile.TemporaryDirectory()

        # 创建测试文本文件
        self.test_txt_file = os.path.join(self.temp_dir.name, "test.txt")
        with open(self.test_txt_file, "w", encoding="utf-8") as f:
            f.write("这是一个测试文本文件。\n测试内容。")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_txt_document(self):
        """测试加载文本文件"""
        documents = self.loader.load_document(self.test_txt_file)
        self.assertEqual(len(documents), 1)
        self.assertIn("这是一个测试文本文件", documents[0].page_content)
        self.assertEqual(documents[0].metadata["source"], self.test_txt_file)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_document("non_existent_file.txt")

    def test_load_unsupported_file_type(self):
        """测试加载不支持的文件类型"""
        # 创建一个不支持的文件类型
        unsupported_file = os.path.join(self.temp_dir.name, "test.unsupported")
        with open(unsupported_file, "w", encoding="utf-8") as f:
            f.write("测试内容")

        with self.assertRaises(ValueError):
            self.loader.load_document(unsupported_file)

    def test_load_pdf_without_pypdf(self):
        """测试在没有 pypdf 的情况下加载 PDF 文件"""
        import sys

        # 保存原始状态
        original_modules = dict(sys.modules)

        # 确保 pypdf 不在模块中
        if "pypdf" in sys.modules:
            del sys.modules["pypdf"]

        try:
            # 直接尝试导入 pypdf
            import pypdf  # noqa: F401

            # 如果导入成功，说明环境中已安装 pypdf，跳过测试
            self.skipTest("pypdf is installed, skipping test")
        except ImportError:
            # 如果导入失败，说明测试环境正确
            pass

        # 现在测试 _load_pdf 方法
        try:
            with self.assertRaises(ImportError):
                # 直接调用 _load_pdf 方法
                self.loader._load_pdf("test.pdf")
        finally:
            # 恢复原始模块状态
            sys.modules.update(original_modules)

    def test_load_docx_without_python_docx(self):
        """测试在未安装 python-docx 时加载 DOCX 文件"""
        # 创建测试 DOCX 文件
        test_docx_file = os.path.join(self.temp_dir.name, "test.docx")
        # 创建一个简单的文件（即使不是真正的 DOCX 格式）
        with open(test_docx_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 使用 mock 来模拟 ImportError
        with patch(
            "langchain_llm_toolkit.document_loader.DocumentLoader._load_docx"
        ) as mock_load:
            mock_load.side_effect = ImportError("需要安装 python-docx 来处理 DOCX 文件")

            with self.assertRaises(ImportError):
                self.loader.load_document(test_docx_file)

    def test_load_empty_txt_file(self):
        """测试加载空文本文件"""
        empty_file = os.path.join(self.temp_dir.name, "empty.txt")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("")

        documents = self.loader.load_document(empty_file)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, "")

    def test_load_txt_with_different_encodings(self):
        """测试加载不同编码的文本文件"""
        # UTF-8 编码
        utf8_file = os.path.join(self.temp_dir.name, "utf8.txt")
        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write("UTF-8 编码测试")

        documents = self.loader.load_document(utf8_file)
        self.assertIn("UTF-8", documents[0].page_content)

        # GBK 编码
        gbk_file = os.path.join(self.temp_dir.name, "gbk.txt")
        with open(gbk_file, "w", encoding="gbk") as f:
            f.write("GBK 编码测试")

        documents = self.loader.load_document(gbk_file)
        self.assertEqual(len(documents), 1)

    def test_load_large_txt_file(self):
        """测试加载大文本文件"""
        large_file = os.path.join(self.temp_dir.name, "large.txt")
        large_content = "测试内容\n" * 10000

        with open(large_file, "w", encoding="utf-8") as f:
            f.write(large_content)

        documents = self.loader.load_document(large_file)
        self.assertEqual(len(documents), 1)
        self.assertGreater(len(documents[0].page_content), 10000)

    def test_load_txt_with_special_characters(self):
        """测试加载包含特殊字符的文本文件"""
        special_file = os.path.join(self.temp_dir.name, "special.txt")
        special_content = "特殊字符：\n\t换行和制表符\n\"引号\"\n'单引号'\n反斜杠\\"

        with open(special_file, "w", encoding="utf-8") as f:
            f.write(special_content)

        documents = self.loader.load_document(special_file)
        self.assertIn("特殊字符", documents[0].page_content)
        self.assertIn("换行和制表符", documents[0].page_content)

    def test_load_txt_with_multiline_content(self):
        """测试加载多行文本文件"""
        multiline_file = os.path.join(self.temp_dir.name, "multiline.txt")
        lines = [f"第{i}行内容" for i in range(1, 101)]

        with open(multiline_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        documents = self.loader.load_document(multiline_file)
        self.assertIn("第1行内容", documents[0].page_content)
        self.assertIn("第100行内容", documents[0].page_content)

    def test_load_txt_preserves_metadata(self):
        """测试文本文件元数据保留"""
        documents = self.loader.load_document(self.test_txt_file)
        self.assertEqual(len(documents), 1)
        self.assertIn("source", documents[0].metadata)
        self.assertEqual(documents[0].metadata["source"], self.test_txt_file)

    def test_load_multiple_files_sequentially(self):
        """测试顺序加载多个文件"""
        files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir.name, f"test{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"文件{i}内容")
            files.append(file_path)

        all_documents = []
        for file_path in files:
            docs = self.loader.load_document(file_path)
            all_documents.extend(docs)

        self.assertEqual(len(all_documents), 3)

    def test_load_file_with_absolute_path(self):
        """测试使用绝对路径加载文件"""
        abs_path = os.path.abspath(self.test_txt_file)
        documents = self.loader.load_document(abs_path)
        self.assertEqual(len(documents), 1)

    def test_load_file_with_relative_path(self):
        """测试使用相对路径加载文件"""
        # 切换到临时目录
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir.name)
            documents = self.loader.load_document("test.txt")
            self.assertEqual(len(documents), 1)
        finally:
            os.chdir(original_cwd)

    def test_load_txt_with_chinese_and_english(self):
        """测试加载中英文混合文本"""
        mixed_file = os.path.join(self.temp_dir.name, "mixed.txt")
        mixed_content = "中文内容\nEnglish Content\n混合 Mixed 内容"

        with open(mixed_file, "w", encoding="utf-8") as f:
            f.write(mixed_content)

        documents = self.loader.load_document(mixed_file)
        self.assertIn("中文内容", documents[0].page_content)
        self.assertIn("English Content", documents[0].page_content)

    def test_load_txt_with_code_content(self):
        """测试加载包含代码的文本文件"""
        code_file = os.path.join(self.temp_dir.name, "code.txt")
        code_content = """
def hello_world():
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self):
        self.name = "Test"
"""

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code_content)

        documents = self.loader.load_document(code_file)
        self.assertIn("def hello_world", documents[0].page_content)
        self.assertIn("class TestClass", documents[0].page_content)

    def test_load_txt_with_markdown(self):
        """测试加载 Markdown 格式文本"""
        md_file = os.path.join(self.temp_dir.name, "test_markdown.txt")
        md_content = """
# 标题

## 二级标题

- 列表项1
- 列表项2

**粗体** 和 *斜体*

```python
code block
```
"""

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        documents = self.loader.load_document(md_file)
        self.assertIn("# 标题", documents[0].page_content)
        self.assertIn("**粗体**", documents[0].page_content)

    def test_load_txt_with_unicode_characters(self):
        """测试加载包含 Unicode 字符的文本"""
        unicode_file = os.path.join(self.temp_dir.name, "unicode.txt")
        unicode_content = "Emoji: 😀 🎉 🚀\nSymbols: © ® ™ € £ ¥\nMath: ∑ ∫ √ ∞"

        with open(unicode_file, "w", encoding="utf-8") as f:
            f.write(unicode_content)

        documents = self.loader.load_document(unicode_file)
        self.assertIn("😀", documents[0].page_content)
        self.assertIn("©", documents[0].page_content)
        self.assertIn("∑", documents[0].page_content)

    def test_load_txt_with_only_whitespace(self):
        """测试加载只包含空白的文本文件"""
        whitespace_file = os.path.join(self.temp_dir.name, "whitespace.txt")
        with open(whitespace_file, "w", encoding="utf-8") as f:
            f.write("   \n\n\t\t\n   ")

        documents = self.loader.load_document(whitespace_file)
        self.assertEqual(len(documents), 1)
        self.assertIn("   ", documents[0].page_content)

    def test_load_txt_with_long_lines(self):
        """测试加载包含长行的文本文件"""
        long_line_file = os.path.join(self.temp_dir.name, "long_line.txt")
        long_line = "A" * 10000
        content = f"{long_line}\n短行\n{long_line}"

        with open(long_line_file, "w", encoding="utf-8") as f:
            f.write(content)

        documents = self.loader.load_document(long_line_file)
        self.assertEqual(len(documents), 1)
        self.assertGreater(len(documents[0].page_content), 20000)

    def test_load_txt_with_mixed_line_endings(self):
        """测试加载包含混合换行符的文本"""
        mixed_file = os.path.join(self.temp_dir.name, "mixed_endings.txt")
        content = "Line1\nLine2\r\nLine3\rLine4"

        with open(mixed_file, "w", encoding="utf-8", newline="") as f:
            f.write(content)

        documents = self.loader.load_document(mixed_file)
        self.assertIn("Line1", documents[0].page_content)
        self.assertIn("Line2", documents[0].page_content)
        self.assertIn("Line3", documents[0].page_content)
        self.assertIn("Line4", documents[0].page_content)

    def test_load_txt_with_tabs(self):
        """测试加载包含制表符的文本"""
        tab_file = os.path.join(self.temp_dir.name, "tabs.txt")
        content = "Column1\tColumn2\tColumn3\nData1\tData2\tData3"

        with open(tab_file, "w", encoding="utf-8") as f:
            f.write(content)

        documents = self.loader.load_document(tab_file)
        self.assertIn("\t", documents[0].page_content)
        self.assertIn("Column1", documents[0].page_content)

    def test_load_txt_preserves_newlines(self):
        """测试加载文本文件保留换行符"""
        newline_file = os.path.join(self.temp_dir.name, "newlines.txt")
        content = "Line1\n\nLine3\n\n\nLine6"

        with open(newline_file, "w", encoding="utf-8") as f:
            f.write(content)

        documents = self.loader.load_document(newline_file)
        self.assertIn("\n\n", documents[0].page_content)

    def test_load_txt_with_binary_like_content(self):
        """测试加载类似二进制内容的文本"""
        binary_like_file = os.path.join(self.temp_dir.name, "binary_like.txt")
        content = "\x00\x01\x02\x03Some text\x04\x05"

        with open(binary_like_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)

        documents = self.loader.load_document(binary_like_file)
        self.assertEqual(len(documents), 1)

    def test_load_document_with_symlink(self):
        """测试加载符号链接文件"""
        original_file = os.path.join(self.temp_dir.name, "original.txt")
        with open(original_file, "w", encoding="utf-8") as f:
            f.write("原始文件内容")

        symlink_file = os.path.join(self.temp_dir.name, "symlink.txt")
        try:
            os.symlink(original_file, symlink_file)
            documents = self.loader.load_document(symlink_file)
            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].page_content, "原始文件内容")
        except OSError:
            self.skipTest("系统不支持符号链接")

    def test_load_document_case_insensitive_extension(self):
        """测试文件扩展名大小写不敏感"""
        upper_file = os.path.join(self.temp_dir.name, "test.TXT")
        with open(upper_file, "w", encoding="utf-8") as f:
            f.write("测试内容")

        documents = self.loader.load_document(upper_file)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, "测试内容")

    def test_load_txt_with_json_content(self):
        """测试加载 JSON 格式内容"""
        json_file = os.path.join(self.temp_dir.name, "data.txt")
        json_content = '{"name": "测试", "value": 123, "items": ["a", "b", "c"]}'

        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json_content)

        documents = self.loader.load_document(json_file)
        self.assertIn('"name"', documents[0].page_content)
        self.assertIn('"测试"', documents[0].page_content)

    def test_load_txt_with_xml_content(self):
        """测试加载 XML 格式内容"""
        xml_file = os.path.join(self.temp_dir.name, "data.txt")
        xml_content = '<?xml version="1.0"?><root><item>测试</item></root>'

        with open(xml_file, "w", encoding="utf-8") as f:
            f.write(xml_content)

        documents = self.loader.load_document(xml_file)
        self.assertIn("<?xml", documents[0].page_content)
        self.assertIn("<item>测试</item>", documents[0].page_content)

    def test_load_multiple_files_with_same_content(self):
        """测试加载多个相同内容的文件"""
        content = "相同的内容"

        for i in range(3):
            file_path = os.path.join(self.temp_dir.name, f"same_{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            documents = self.loader.load_document(file_path)
            self.assertEqual(documents[0].page_content, content)
            self.assertEqual(documents[0].metadata["source"], file_path)

    def test_load_txt_with_path_containing_spaces(self):
        """测试加载路径包含空格的文件"""
        space_dir = os.path.join(self.temp_dir.name, "path with spaces")
        os.makedirs(space_dir)

        space_file = os.path.join(space_dir, "file with spaces.txt")
        with open(space_file, "w", encoding="utf-8") as f:
            f.write("内容测试")

        documents = self.loader.load_document(space_file)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, "内容测试")

    def test_load_txt_with_path_containing_unicode(self):
        """测试加载路径包含 Unicode 字符的文件"""
        unicode_dir = os.path.join(self.temp_dir.name, "中文目录")
        os.makedirs(unicode_dir)

        unicode_file = os.path.join(unicode_dir, "中文文件.txt")
        with open(unicode_file, "w", encoding="utf-8") as f:
            f.write("中文内容")

        documents = self.loader.load_document(unicode_file)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, "中文内容")


if __name__ == "__main__":
    unittest.main()

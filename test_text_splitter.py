import unittest
from text_splitter import TextSplitter
from langchain_core.documents import Document


class TestTextSplitter(unittest.TestCase):
    def setUp(self):
        self.splitter = TextSplitter()

    def test_split_documents_recursive(self):
        """测试使用递归方法分割文档"""
        # 创建测试文档
        test_doc = Document(
            page_content="这是一个测试文档。\n\n这是第二段落。\n这是第三段落。",
            metadata={"source": "test.txt"},
        )

        # 分割文档
        split_docs = self.splitter.split_documents(
            [test_doc], chunk_size=20, chunk_overlap=5, method="recursive"
        )

        # 验证分割结果
        self.assertGreater(len(split_docs), 1)
        for doc in split_docs:
            self.assertLessEqual(len(doc.page_content), 20)

    def test_split_documents_character(self):
        """测试使用字符方法分割文档"""
        # 创建测试文档
        test_doc = Document(
            page_content="12345678901234567890", metadata={"source": "test.txt"}  # 20个字符
        )

        # 分割文档
        split_docs = self.splitter.split_documents(
            [test_doc], chunk_size=5, chunk_overlap=1, method="character"
        )

        # 验证分割结果
        self.assertGreater(len(split_docs), 1)
        for doc in split_docs:
            self.assertLessEqual(len(doc.page_content), 5)

    def test_split_documents_invalid_method(self):
        """测试使用无效的分割方法"""
        # 创建测试文档
        test_doc = Document(page_content="这是一个测试文档。", metadata={"source": "test.txt"})

        # 验证异常
        with self.assertRaises(ValueError):
            self.splitter.split_documents([test_doc], method="invalid")

    def test_split_text_recursive(self):
        """测试使用递归方法分割文本"""
        test_text = "这是一个测试文本。\n\n这是第二段落。\n这是第三段落。"

        # 分割文本
        split_texts = self.splitter.split_text(
            test_text, chunk_size=20, chunk_overlap=5, method="recursive"
        )

        # 验证分割结果
        self.assertGreater(len(split_texts), 1)
        for text in split_texts:
            self.assertLessEqual(len(text), 20)

    def test_split_text_character(self):
        """测试使用字符方法分割文本"""
        test_text = "12345678901234567890"  # 20个字符

        # 分割文本
        split_texts = self.splitter.split_text(
            test_text, chunk_size=5, chunk_overlap=1, method="character"
        )

        # 验证分割结果
        self.assertGreater(len(split_texts), 1)
        for text in split_texts:
            self.assertLessEqual(len(text), 5)

    def test_split_text_invalid_method(self):
        """测试使用无效的分割方法"""
        test_text = "这是一个测试文本。"

        # 验证异常
        with self.assertRaises(ValueError):
            self.splitter.split_text(test_text, method="invalid")


if __name__ == "__main__":
    unittest.main()

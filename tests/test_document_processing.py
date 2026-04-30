import os
import tempfile
from langchain_llm_toolkit.document_loader import DocumentLoader
from langchain_llm_toolkit.text_splitter import TextSplitter


def test_document_loader():
    """测试文档加载器"""
    print("测试文档加载器...")

    # 创建测试文件
    test_files = []

    # 创建测试 TXT 文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("这是一个测试文本文件。\n包含多行内容。\n用于测试文档加载功能。")
        test_files.append(f.name)

    # 创建文档加载器实例
    loader = DocumentLoader()

    # 测试加载 TXT 文件
    try:
        documents = loader.load_document(test_files[0])
        print(f"成功加载 TXT 文件，获取到 {len(documents)} 个文档")
        print(f"文档内容: {documents[0].page_content[:100]}...")
    except Exception as e:
        print(f"加载 TXT 文件失败: {e}")

    # 清理测试文件
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)

    print("文档加载器测试完成！")


def test_text_splitter():
    """测试文本分割器"""
    print("\n测试文本分割器...")

    # 创建测试文本
    test_text = "这是一个测试文本。" * 50  # 生成较长的文本

    # 创建文本分割器实例
    splitter = TextSplitter()

    # 测试分割文本
    try:
        chunks = splitter.split_text(test_text, chunk_size=100, chunk_overlap=20)
        print(f"成功分割文本，获取到 {len(chunks)} 个片段")
        for i, chunk in enumerate(chunks[:3]):  # 只显示前3个片段
            print(f"片段 {i + 1}: {chunk[:50]}...")
    except Exception as e:
        print(f"分割文本失败: {e}")

    print("文本分割器测试完成！")


def test_complete_document_processing():
    """测试完整的文档处理流程"""
    print("\n测试完整的文档处理流程...")

    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("这是一个测试文档。\n" * 20)  # 生成多行文本
        test_file = f.name

    try:
        # 加载文档
        loader = DocumentLoader()
        documents = loader.load_document(test_file)
        print(f"成功加载文档，获取到 {len(documents)} 个文档")

        # 分割文档
        splitter = TextSplitter()
        split_docs = splitter.split_documents(
            documents, chunk_size=150, chunk_overlap=30
        )
        print(f"成功分割文档，获取到 {len(split_docs)} 个片段")

        # 显示分割结果
        for i, doc in enumerate(split_docs[:2]):  # 只显示前2个片段
            print(f"片段 {i + 1} 长度: {len(doc.page_content)}")
            print(f"内容: {doc.page_content[:100]}...")
    except Exception as e:
        print(f"文档处理失败: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

    print("完整文档处理流程测试完成！")


if __name__ == "__main__":
    test_document_loader()
    test_text_splitter()
    test_complete_document_processing()

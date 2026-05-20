"""
Tests for Document Import Manager.
文档导入管理器测试
"""

import tempfile
from pathlib import Path

from langchain_llm_toolkit.document_import_manager import (
    DocumentImportManager,
    ImportReport,
    ImportResult,
)


class TestImportResult:
    """测试导入结果"""

    def test_success_result(self):
        """测试成功结果"""
        result = ImportResult(
            file_path="/test/doc.txt",
            success=True,
            documents_count=10,
        )
        assert result.success is True
        assert result.documents_count == 10
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = ImportResult(
            file_path="/test/doc.txt",
            success=False,
            error="File not found",
        )
        assert result.success is False
        assert result.documents_count == 0
        assert result.error == "File not found"


class TestImportReport:
    """测试导入报告"""

    def test_empty_report(self):
        """测试空报告"""
        report = ImportReport()
        assert report.total_files == 0
        assert report.successful_files == 0
        assert report.failed_files == 0
        assert report.total_documents == 0

    def test_get_summary(self):
        """测试获取摘要"""
        report = ImportReport(
            total_files=10,
            successful_files=8,
            failed_files=2,
            total_documents=100,
        )
        summary = report.get_summary()
        assert summary["total_files"] == 10
        assert summary["successful_files"] == 8
        assert "success_rate" in summary


class TestDocumentImportManager:
    """测试文档导入管理器"""

    def test_init(self):
        """测试初始化"""
        manager = DocumentImportManager()
        assert manager is not None
        assert manager.max_workers == 4

    def test_import_file_not_exists(self):
        """测试导入不存在的文件"""
        manager = DocumentImportManager()
        result = manager.import_file("/nonexistent/file.txt")
        assert result.success is False
        assert result.error is not None

    def test_import_file_txt(self):
        """测试导入文本文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document.\n" * 10)
            temp_path = f.name

        try:
            manager = DocumentImportManager()
            result = manager.import_file(temp_path)
            assert result.success is True
            assert result.documents_count > 0
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_import_file_md(self):
        """测试导入 Markdown 文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Document\n\nThis is a test.\n\n## Section\n\nMore content.")
            temp_path = f.name

        try:
            manager = DocumentImportManager()
            result = manager.import_file(temp_path)
            assert result.success is True
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_import_files(self):
        """测试批量导入文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = Path(temp_dir) / "doc2.txt"

            file1.write_text("Document 1 content.")
            file2.write_text("Document 2 content.")

            manager = DocumentImportManager()
            report = manager.import_files([str(file1), str(file2)])

            assert report.total_files == 2
            assert report.successful_files >= 0

    def test_import_directory(self):
        """测试导入目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = Path(temp_dir) / "doc2.md"

            file1.write_text("Document 1 content.")
            file2.write_text("Document 2 content.")

            manager = DocumentImportManager()
            report = manager.import_directory(temp_dir)

            assert report.total_files >= 2

    def test_scan_directory(self):
        """测试扫描目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = Path(temp_dir) / "doc2.md"

            file1.write_text("Content 1.")
            file2.write_text("Content 2.")

            manager = DocumentImportManager()
            files = manager.scan_directory(temp_dir)

            assert len(files) >= 2

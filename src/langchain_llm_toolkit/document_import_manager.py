"""
Document Import Manager - 文档导入管理器
支持批量导入、目录扫描、进度跟踪
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from langchain_llm_toolkit.document_loader import DocumentLoader
from langchain_llm_toolkit.logger import logger


@dataclass
class ImportResult:
    """导入结果"""

    file_path: str
    success: bool
    documents_count: int = 0
    error: str | None = None
    processing_time: float = 0.0


@dataclass
class ImportReport:
    """导入报告"""

    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_documents: int = 0
    total_chunks: int = 0
    processing_time: float = 0.0
    results: list[ImportResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def get_summary(self) -> dict:
        return {
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "success_rate": f"{(self.successful_files / max(self.total_files, 1)) * 100:.1f}%",
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "processing_time": f"{self.processing_time:.2f}s",
        }


class DocumentImportManager:
    """文档导入管理器"""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".pdf", ".txt", ".md", ".docx"}

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        max_workers: int = 4,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.loader = document_loader or DocumentLoader()
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def import_file(self, file_path: str) -> ImportResult:
        """导入单个文件"""
        start_time = datetime.now()

        try:
            if not os.path.exists(file_path):
                return ImportResult(
                    file_path=file_path,
                    success=False,
                    error=f"文件不存在: {file_path}",
                )

            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                return ImportResult(
                    file_path=file_path,
                    success=False,
                    error=f"不支持的文件类型: {file_ext}",
                )

            documents = self.loader.load_document(file_path)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"导入文件成功: {file_path} ({len(documents)} 个文档)")

            return ImportResult(
                file_path=file_path,
                success=True,
                documents_count=len(documents),
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"导入文件失败: {file_path} - {e}")
            return ImportResult(
                file_path=file_path,
                success=False,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def import_files(
        self,
        file_paths: list[str],
        parallel: bool = True,
    ) -> ImportReport:
        """批量导入文件"""
        start_time = datetime.now()
        report = ImportReport(total_files=len(file_paths))

        if parallel and len(file_paths) > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.import_file, fp): fp for fp in file_paths}

                for future in as_completed(futures):
                    result = future.result()
                    report.results.append(result)

                    if result.success:
                        report.successful_files += 1
                        report.total_documents += result.documents_count
                    else:
                        report.failed_files += 1
                        if result.error:
                            report.errors.append(f"{result.file_path}: {result.error}")
        else:
            for file_path in file_paths:
                result = self.import_file(file_path)
                report.results.append(result)

                if result.success:
                    report.successful_files += 1
                    report.total_documents += result.documents_count
                else:
                    report.failed_files += 1
                    if result.error:
                        report.errors.append(f"{result.file_path}: {result.error}")

        report.processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"批量导入完成: {report.successful_files}/{report.total_files} 成功, "
            f"{report.total_documents} 个文档, {report.processing_time:.2f}s"
        )

        return report

    def import_directory(
        self,
        directory: str,
        recursive: bool = True,
        exclude_patterns: list[str] | None = None,
    ) -> ImportReport:
        """导入目录中的所有文档"""
        directory_path = Path(directory)

        if not directory_path.exists():
            return ImportReport(
                total_files=0,
                errors=[f"目录不存在: {directory}"],
            )

        exclude_patterns = exclude_patterns or []
        file_paths = []

        pattern = "**/*" if recursive else "*"

        for file_path in directory_path.glob(pattern):
            if not file_path.is_file():
                continue

            file_ext = file_path.suffix.lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                continue

            relative_path = file_path.relative_to(directory_path)
            should_exclude = False

            for pattern in exclude_patterns:
                if pattern in str(relative_path):
                    should_exclude = True
                    break

            if not should_exclude:
                file_paths.append(str(file_path))

        logger.info(f"发现 {len(file_paths)} 个文档文件在 {directory}")

        return self.import_files(file_paths, parallel=True)

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> dict:
        """扫描目录，返回文档统计"""
        directory_path = Path(directory)

        if not directory_path.exists():
            return {"error": f"目录不存在: {directory}"}

        stats = {
            "total_files": 0,
            "by_extension": {},
            "total_size": 0,
            "files": [],
        }

        pattern = "**/*" if recursive else "*"

        for file_path in directory_path.glob(pattern):
            if not file_path.is_file():
                continue

            file_ext = file_path.suffix.lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                continue

            file_size = file_path.stat().st_size

            stats["total_files"] += 1
            stats["total_size"] += file_size

            if file_ext not in stats["by_extension"]:
                stats["by_extension"][file_ext] = {"count": 0, "size": 0}

            stats["by_extension"][file_ext]["count"] += 1
            stats["by_extension"][file_ext]["size"] += file_size

            stats["files"].append(
                {
                    "path": str(file_path),
                    "extension": file_ext,
                    "size": file_size,
                }
            )

        stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)

        return stats

    def get_supported_extensions(self) -> list[str]:
        """获取支持的文件扩展名"""
        return list(self.SUPPORTED_EXTENSIONS)


document_import_manager = DocumentImportManager()

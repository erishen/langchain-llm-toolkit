import logging
import tempfile
import os

from langchain_llm_toolkit.logger import setup_logging, logger


class TestSetupLogging:
    """测试日志设置"""

    def test_setup_logging_default(self):
        """测试默认日志设置"""
        root_logger = setup_logging()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_setup_logging_debug_level(self):
        """测试 DEBUG 日志级别"""
        root_logger = setup_logging(log_level="DEBUG")

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_warning_level(self):
        """测试 WARNING 日志级别"""
        root_logger = setup_logging(log_level="WARNING")

        assert root_logger.level == logging.WARNING

    def test_setup_logging_error_level(self):
        """测试 ERROR 日志级别"""
        root_logger = setup_logging(log_level="ERROR")

        assert root_logger.level == logging.ERROR

    def test_setup_logging_critical_level(self):
        """测试 CRITICAL 日志级别"""
        root_logger = setup_logging(log_level="CRITICAL")

        assert root_logger.level == logging.CRITICAL

    def test_setup_logging_with_file(self):
        """测试日志文件设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "test.log")
            root_logger = setup_logging(log_file=log_file)

            assert os.path.exists(os.path.dirname(log_file))
            assert len(root_logger.handlers) == 2

    def test_setup_logging_creates_log_directory(self):
        """测试创建日志目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "nested", "logs", "test.log")
            setup_logging(log_file=log_file)

            assert os.path.exists(os.path.dirname(log_file))

    def test_setup_logging_clears_existing_handlers(self):
        """测试清除现有处理器"""
        root_logger = logging.getLogger()

        root_logger.addHandler(logging.StreamHandler())
        root_logger.addHandler(logging.StreamHandler())
        initial_count = len(root_logger.handlers)

        root_logger = setup_logging()

        assert len(root_logger.handlers) < initial_count

    def test_setup_logging_console_handler(self):
        """测试控制台处理器"""
        root_logger = setup_logging()

        has_console_handler = any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, logging.handlers.RotatingFileHandler)
            for handler in root_logger.handlers
        )

        assert has_console_handler

    def test_setup_logging_file_handler(self):
        """测试文件处理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            root_logger = setup_logging(log_file=log_file)

            has_file_handler = any(
                isinstance(handler, logging.handlers.RotatingFileHandler)
                for handler in root_logger.handlers
            )

            assert has_file_handler

    def test_setup_logging_formatter(self):
        """测试日志格式"""
        root_logger = setup_logging()

        for handler in root_logger.handlers:
            if handler.formatter:
                assert "%(asctime)s" in handler.formatter._fmt
                assert "%(name)s" in handler.formatter._fmt
                assert "%(levelname)s" in handler.formatter._fmt
                assert "%(message)s" in handler.formatter._fmt

    def test_setup_logging_case_insensitive(self):
        """测试日志级别大小写不敏感"""
        root_logger = setup_logging(log_level="info")

        assert root_logger.level == logging.INFO

        root_logger = setup_logging(log_level="Debug")

        assert root_logger.level == logging.DEBUG


class TestLogger:
    """测试日志器"""

    def test_logger_instance(self):
        """测试日志器实例"""
        assert isinstance(logger, logging.Logger)
        assert logger.name == "langchain_project"

    def test_logger_can_log_info(self, capfd):
        """测试日志器可以记录 INFO"""
        setup_logging(log_level="DEBUG")

        logger.info("Test info message")

        captured = capfd.readouterr()
        assert "Test info message" in captured.out

    def test_logger_can_log_debug(self, capfd):
        """测试日志器可以记录 DEBUG"""
        setup_logging(log_level="DEBUG")

        logger.debug("Test debug message")

        captured = capfd.readouterr()
        assert "Test debug message" in captured.out

    def test_logger_can_log_warning(self, capfd):
        """测试日志器可以记录 WARNING"""
        setup_logging(log_level="DEBUG")

        logger.warning("Test warning message")

        captured = capfd.readouterr()
        assert "Test warning message" in captured.out

    def test_logger_can_log_error(self, capfd):
        """测试日志器可以记录 ERROR"""
        setup_logging(log_level="DEBUG")

        logger.error("Test error message")

        captured = capfd.readouterr()
        assert "Test error message" in captured.out

    def test_logger_can_log_critical(self, capfd):
        """测试日志器可以记录 CRITICAL"""
        setup_logging(log_level="DEBUG")

        logger.critical("Test critical message")

        captured = capfd.readouterr()
        assert "Test critical message" in captured.out

    def test_logger_writes_to_file(self):
        """测试日志写入文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(log_level="INFO", log_file=log_file)

            logger.info("Test file message")

            with open(log_file, "r") as f:
                content = f.read()
                assert "Test file message" in content

    def test_logger_respects_level(self, capfd):
        """测试日志器遵守日志级别"""
        setup_logging(log_level="WARNING")

        logger.info("This should not be logged")
        logger.warning("This should be logged")

        captured = capfd.readouterr()
        assert "This should not be logged" not in captured.out
        assert "This should be logged" in captured.out

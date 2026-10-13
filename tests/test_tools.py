"""使用标准库 unittest 对工具与离线引擎进行基本测试。"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codeagent.tools import build_default_registry
from codeagent.offline import OfflineEngine


class TestTools(unittest.TestCase):
    def setUp(self):
        self.reg = build_default_registry()
        self.tmp = tempfile.mkdtemp()

    def test_run_code(self):
        out = self.reg.execute("run_code", {"code": "print(1+1)"})
        self.assertIn("2", out)

    def test_run_code_timeout(self):
        out = self.reg.execute("run_code", {"code": "while True: pass", "timeout": 1})
        self.assertIn("超时", out)

    def test_read_and_list(self):
        path = os.path.join(self.tmp, "a.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        content = self.reg.execute("read_file", {"path": path})
        self.assertIn("x = 1", content)
        listed = self.reg.execute("list_dir", {"path": self.tmp})
        self.assertIn("a.py", listed)

    def test_search(self):
        path = os.path.join(self.tmp, "b.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("def hello():\n    return 1\n")
        hits = self.reg.execute("search_code", {"pattern": "hello", "path": self.tmp})
        self.assertIn("def hello", hits)


class TestOffline(unittest.TestCase):
    def setUp(self):
        self.reg = build_default_registry()
        self.engine = OfflineEngine(self.reg)
        self.tmp = tempfile.mkdtemp()

    def test_review_detects_issues(self):
        path = os.path.join(self.tmp, "bad.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("password = '123'\ndef f(x):\n    try:\n        return x\n    except:\n        pass\n")
        report = self.engine.review_file(path)
        self.assertIn("代码审查报告", report)
        self.assertTrue("硬编码" in report or "except" in report or "docstring" in report)

    def test_explain_structure(self):
        path = os.path.join(self.tmp, "good.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("def add(a, b):\n    \"\"\"add two numbers\"\"\"\n    return a + b\n")
        text = self.engine.explain_file(path)
        self.assertIn("add", text)
        self.assertIn("代码解释", text)

    def test_dispatch_help(self):
        self.assertIn("离线模式命令", self.engine.dispatch("help"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

import os
import unittest
from src.core.tools.filesystem_tools import (
    view_file_tool,
    write_file_tool,
    replace_file_content_tool,
    grep_search_tool,
    list_dir_tool,
)
from src.core.tools.audit_testing_tools import (
    audit_artifact_tool,
    run_agent_tests_tool,
    improve_artifact_tool,
)


class TestUnifiedTools(unittest.TestCase):
    def test_filesystem_tools_lifecycle(self):
        test_path = "sandboxes/scratch_test_tool.txt"
        
        # Write
        res_w = write_file_tool.invoke({"path": test_path, "content": "Line 1\nLine 2\nLine 3\n", "overwrite": True})
        self.assertEqual(res_w["status"], "success")

        # View
        res_v = view_file_tool.invoke({"path": test_path, "start_line": 1, "end_line": 2})
        self.assertIn("Line 1", res_v["content"])

        # Replace
        res_r = replace_file_content_tool.invoke({
            "path": test_path,
            "target_content": "Line 2",
            "replacement_content": "Line 2 Replaced"
        })
        self.assertEqual(res_r["status"], "success")

        # Grep
        res_g = grep_search_tool.invoke({"search_path": "sandboxes", "query": "Replaced"})
        self.assertTrue(len(res_g) >= 1)

        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)

    def test_audit_testing_tools(self):
        # Audit tool
        audit_res = audit_artifact_tool.invoke({"target_name": "calc_prompt", "content": "Please calculate numbers"})
        self.assertIn("NEEDS_IMPROVEMENT", audit_res["status"])

        # Improve tool
        imp_res = improve_artifact_tool.invoke({"target_name": "calc_prompt", "content": "Please calculate numbers"})
        self.assertEqual(imp_res["status"], "REMEDIATED")


if __name__ == "__main__":
    unittest.main()

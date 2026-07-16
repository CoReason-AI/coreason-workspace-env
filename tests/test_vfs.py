import unittest
from unittest.mock import MagicMock, AsyncMock
from src.core.vfs.git_backend import TrueGitBackend
from src.core.vfs.crdt_sync import CRDTSyncManager


class TestProjectWorkspace(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.git_backend = TrueGitBackend(workspace_path="./test_repo")
        self.crdt = CRDTSyncManager()

    def test_git_backend_initialization(self):
        """Test TrueGitBackend."""
        # Test that the commit_changes method doesn't crash on mock data
        # Note: We are abstracting the actual git binary execution for this unit test
        # We need to mock _run_git so it doesn't fail if git is not initialized cleanly in /tmp
        self.git_backend._run_git = MagicMock(return_value="mock_status")
        self.git_backend.commit_changes(author="agent-123", message="Test automated commit")
        self.git_backend._run_git.assert_called()

    async def test_crdt_sync_manager(self):
        """Test Client Registration for CRDT."""
        mock_websocket = AsyncMock()
        await self.crdt.connect_client("doc-1", mock_websocket)
        self.assertIn("doc-1", self.crdt.active_documents)
        
        await self.crdt.disconnect_client("doc-1", mock_websocket)
        self.assertNotIn("doc-1", self.crdt.active_documents)



if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch, ANY
import time
from proxy.metrics import MetricsCollector

class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        # Reset singleton if needed or just patch around it
        # Since it's a singleton, we need to be careful.
        # We can re-instantiate or clear state.
        MetricsCollector._instance = None
        self.collector = MetricsCollector()
        self.collector.db = MagicMock() # Mock Firestore DB
        self.collector.local_buffer.clear()
        self.collector.sync_threshold = 2 # Low threshold for testing

    @patch('proxy.metrics.requests.get')
    def test_hardware_fetch(self, mock_get):
        # Mock DNT table response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "node_123": {
                "hardware": {
                    "gpus": [{"name": "NVIDIA A100"}]
                }
            }
        }
        mock_get.return_value = mock_response

        hw_spec = self.collector.get_hardware_spec("node_123", "http://dnt/table")
        self.assertEqual(hw_spec, "1x NVIDIA A100")
        
        # Test cache
        self.collector.get_hardware_spec("node_123", "http://dnt/table")
        mock_get.assert_called_once() # Should be cached

    @patch('threading.Thread')
    @patch('proxy.metrics.requests.get')
    def test_record_and_sync(self, mock_get, mock_thread):
        # Setup hardware mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "node_A": {"hardware": {"gpus": [{"name": "T4"}]}}
        }
        mock_get.return_value = mock_response

        # Record 1st request
        self.collector.record(
            model="gpt-3",
            node_id="node_A",
            dnt_endpoint="http://dnt",
            concurrency=3,
            ttft=0.5,
            latency=1.0,
            throughput=50.0
        )
        
        # Buffer should have 1 entry
        key = ("gpt-3", "1x T4", "2-4")
        self.assertIn(key, self.collector.local_buffer)
        self.assertEqual(self.collector.local_buffer[key]["count"], 1)
        
        # Record 2nd request (hits threshold 2)
        self.collector.record(
            model="gpt-3",
            node_id="node_A",
            dnt_endpoint="http://dnt",
            concurrency=4,
            ttft=0.6,
            latency=1.2,
            throughput=48.0
        )
        
        # Should trigger sync (thread start)
        mock_thread.assert_called_once()
        
        # Verify sync args
        # Thread(target=..., args=...)
        # Note: Depending on how it's called (keywords vs positional), we check call_args properly
        _, kwargs = mock_thread.call_args
        # In metrics.py: threading.Thread(target=..., args=(...))
        self.assertIn('target', kwargs)
        self.assertIn('args', kwargs)
        txn_args = kwargs['args']
        self.assertEqual(txn_args[0], "gpt-3")
        
        # Manually invoke _sync_to_firestore to test transaction logic
        # Mock transaction
        mock_transaction = MagicMock()
        self.collector.db.transaction.return_value = mock_transaction
        
        # Mock doc snapshot
        mock_doc_ref = MagicMock()
        self.collector.db.collection.return_value.document.return_value = mock_doc_ref
        
        # Case 1: New document
        mock_snapshot = MagicMock()
        mock_snapshot.exists = False
        mock_doc_ref.get.return_value = mock_snapshot
        
        stats = {
            "count": 2,
            "total_ttft": 1.1,
            "total_latency": 2.2,
            "total_throughput": 98.0
        }
        
        # We need to test the transactional function passed to transaction()
        # In the code: transaction = self.db.transaction(); update_in_transaction(transaction, ...)
        # But _sync_to_firestore calls update_in_transaction internally.
        # We can just run _sync_to_firestore and verify db calls IF we can mock the transaction decorator behavior.
        # Firestore transaction decorator is tricky to mock.
        # We can mock firestore.transactional to just call the function.
        
        with patch('proxy.metrics.firestore.transactional', side_effect=lambda f: f):
            self.collector._sync_to_firestore("gpt-3", "1x T4", "2-4", stats)
            
            # Verify set was called (since does not exist)
            mock_transaction.set.assert_called_once()
            call_args = mock_transaction.set.call_args
            self.assertEqual(call_args[0][1]["count"], 2)
            self.assertAlmostEqual(call_args[0][1]["avg_latency"], 1.1)

if __name__ == '__main__':
    unittest.main()

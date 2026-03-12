
try:
    from backend.utils import get_hardware_spec
    print("Successfully imported get_hardware_spec from backend.utils")
except ImportError as e:
    print(f"Failed to import get_hardware_spec from backend.utils: {e}")

try:
    from backend.metrics import metrics_collector
    print("Successfully imported metrics_collector from backend.metrics")
except ImportError as e:
    print(f"Failed to import metrics_collector from backend.metrics: {e}")

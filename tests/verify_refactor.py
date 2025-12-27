
try:
    from proxy.utils import get_hardware_spec
    print("Successfully imported get_hardware_spec from proxy.utils")
except ImportError as e:
    print(f"Failed to import get_hardware_spec from proxy.utils: {e}")

try:
    from proxy.metrics import metrics_collector
    print("Successfully imported metrics_collector from proxy.metrics")
except ImportError as e:
    print(f"Failed to import metrics_collector from proxy.metrics: {e}")

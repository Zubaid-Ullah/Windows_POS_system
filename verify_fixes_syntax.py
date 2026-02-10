
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

try:
    from src.ui.views.customer_view import CustomerView
    print("CustomerView imported successfully")
except ImportError as e:
    print(f"Error importing CustomerView: {e}")
except Exception as e:
    print(f"Error loading CustomerView: {e}")

try:
    from src.ui.views.pharmacy.pharmacy_customer_view import PharmacyCustomerView
    print("PharmacyCustomerView imported successfully")
except ImportError as e:
    print(f"Error importing PharmacyCustomerView: {e}")
except Exception as e:
    print(f"Error loading PharmacyCustomerView: {e}")

try:
    from src.utils.camera import capture_image
    print("camera module imported successfully")
except Exception as e:
    print(f"Error importing camera: {e}")

"""
Shared serialization utilities for handling numpy types and other serialization needs.
"""

import numpy as np
from typing import Any, Dict, List


class NumpySerializer:
    """Utility class for converting numpy types to Python types for JSON serialization"""
    
    @staticmethod
    def convert_numpy_types(obj: Any) -> Any:
        """
        Convert numpy types to Python types for JSON serialization.
        
        Args:
            obj: Object that may contain numpy types
            
        Returns:
            Object with numpy types converted to Python types
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {key: NumpySerializer.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [NumpySerializer.convert_numpy_types(item) for item in obj]
        else:
            return obj


def serialize_for_json(obj: Any) -> Any:
    """
    Convenience function to serialize an object for JSON encoding.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    return NumpySerializer.convert_numpy_types(obj) 
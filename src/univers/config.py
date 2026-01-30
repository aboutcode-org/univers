
# univers/config.py

from contextlib import contextmanager

class Config:
    """
    Global configuration for univers library.
    
    Simple configuration for single-threaded use.
    """
    
    def __init__(self):
        self._use_libversion_fallback = False
    
    @property
    def use_libversion_fallback(self):
        """
        Get the current libversion fallback setting.
        
        Returns:
            bool: True if libversion fallback is enabled, False otherwise.
        """
        return self._use_libversion_fallback
    
    @use_libversion_fallback.setter
    def use_libversion_fallback(self, value):
        """
        Set the global libversion fallback setting.
        
        Args:
            value: Boolean value to enable (True) or disable (False) fallback.
        
        Example:
            >>> from univers import config
            >>> config.use_libversion_fallback = True
        """
        self._use_libversion_fallback = bool(value)
    
    @contextmanager
    def libversion_fallback(self, enabled=True):
        """
        Context manager for temporary fallback setting.
        
        Args:
            enabled (bool): Whether to enable fallback within the context.
        
        Example:
            >>> from univers import config
            >>> from univers.versions import PypiVersion
            >>> 
            >>> with config.libversion_fallback(enabled=True):
            ...     v1 = PypiVersion("1.2.3-custom")
            ...     v2 = PypiVersion("1.2.4-custom")
            ...     result = v1 < v2
        """
        old_value = self._use_libversion_fallback
        self._use_libversion_fallback = enabled
        try:
            yield
        finally:
            self._use_libversion_fallback = old_value

# Global config instance

config = Config()
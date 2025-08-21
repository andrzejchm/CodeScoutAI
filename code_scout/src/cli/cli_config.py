class CLIConfig:
    """
    Centralized configuration for the CLI application.
    This acts as a singleton-like object to hold global settings.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CLIConfig, cls).__new__(cls)
            cls._instance._is_debug = False  # Default value
        return cls._instance

    @property
    def is_debug(self) -> bool:
        return self._is_debug

    @is_debug.setter
    def is_debug(self, value: bool):
        self._is_debug = value


# Create a single, globally accessible instance
cli_config = CLIConfig()

```json
{
    "testpaths": ["tests"],
    "python_files": ["test_*.py", "*_test.py"],
    "python_classes": ["Test*", "*Test"],
    "python_functions": ["test_*"],
    "norecursedirs": [
        ".git",
        ".tox",
        ".eggs",
        "build",
        "dist",
        "venv",
        "__pycache__"
    ],
    "log_cli": true,
    "log_cli_level": "INFO",
    "log_cli_format": "%(asctime)s [%(levelname)s] %(message)s",
    "log_cli_date_format": "%Y-%m-%d %H:%M:%S",
    "log_file": "logs/pytest.log",
    "log_file_mode": "a",
    "log_file_level": "INFO",
    "log_file_format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "log_file_date_format": "%Y-%m-%d %H:%M:%S",
    "console_output_style": "detailed",
    "doctest_optionflags": ["NORMALIZE_WHITESPACE", "IGNORE_EXCEPTION_DETAIL"],
    "cache_dir": ".pytest_cache",
    "xfail_strict": true,
    "required_plugins": ["pytest-cov"],
    "markers": [
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
        "serial: marks tests as serial (deselect with '-m \"not serial\"')"
    ]
}
```

is not valid under any of the schemas listed in the 'oneOf' keyword

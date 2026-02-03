from __future__ import annotations

import re
import sys


PACKAGE_NAME_REGEX = r"^[-a-zA-Z][-a-zA-Z0-9]+$"
package_name_slug = "{{ cookiecutter.pypi_package_name }}"
if not re.match(PACKAGE_NAME_REGEX, package_name_slug):
    print(
        f"ERROR: The package name {package_name_slug} is not a valid Python module name. Please do not use a _ and use - instead"
    )
    # Exit to cancel project
    sys.exit(1)

PROJECT_SLUG_REGEX = r"^[_a-zA-Z][_a-zA-Z0-9]+$"
project_slug_name = "{{ cookiecutter.project_slug }}"
if not re.match(PROJECT_SLUG_REGEX, project_slug_name):
    print(
        f"ERROR: The project slug {project_slug_name} is not a valid Python module name. Please do not use a - and use _ instead"
    )
    # Exit to cancel project
    sys.exit(1)

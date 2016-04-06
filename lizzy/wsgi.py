"""
Expose application to use with uswgi
"""

from .service import main

application = main(run=False)  # pylint: disable=invalid-name

__all__ = ["distribution", "software", "python", "platform", "revision"]

import pkg_resources
import sys
import git

platform = pkg_resources.get_platform()
python = sys.version
distribution = pkg_resources.get_distribution(__name__.split(".")[0])

software = "{} {}".format(distribution.project_name, distribution.version)

try:
    repo = git.Repo(search_parent_directories=True)
    revision = repo.head.object.hexsha
except git.exc.InvalidGitRepositoryError:
    revision = "UNKNOWN"


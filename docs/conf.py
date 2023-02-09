"""Configuration for sphinx."""
project = "AiiDA Team Compass"
author = "AiiDA Team"
copyright = "AiiDA Team"

extensions = ["myst_parser"]

suppress_warnings = ["myst.header"]
myst_enable_extensions = ["fieldlist"]

html_theme = "furo"
html_title = "AiiDA Team Compass"


import os
from pathlib import Path

from ghapi.all import GhApi
from sphinx.application import Sphinx
from sphinx.util import logging

LOGGER = logging.getLogger("conf")


def setup(app: Sphinx):
    """Setup sphinx."""
    app.connect("builder-inited", update_roadmap)


def update_roadmap(app: Sphinx):
    """Update the roadmap items."""
    if os.environ.get("SKIP_GH_UPDATE", "").lower() == "true":
        LOGGER.info("Skipping GitHub update")
        return

    roadmap_dir = Path(app.srcdir) / "roadmap_items"
    roadmap_dir.mkdir(exist_ok=True)

    current_files = set(roadmap_dir.glob("*.md"))
    read_files = set()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        LOGGER.warning(
            f"No token found at {os.environ.get('GITHUB_TOKEN')}, GitHub "
            "issue information will not be used. "
            "Create a GitHub Personal Access Token and assign it to GITHUB_TOKEN"
            " (see https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)"
        )
        return

    api = GhApi(token=token)
    # see https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28
    for issue in api.issues.list_for_repo("aiidateam", "team-compass", state="open", labels="roadmap/active"):
        LOGGER.info(f"Reading issue {issue['id']}")
        issue_id = issue["id"]
        title = issue["title"]
        body = issue["body"]
        source_url = issue["html_url"]
        plus_one = issue["reactions"]["+1"]

        md_content = (
            f"# {title}\n\n:source: <{source_url}>\n:reactions: {plus_one} 👍\n\n{body}"
        )
        item_path = roadmap_dir.joinpath(f"{issue_id}.md")

        if not (item_path.exists() and item_path.read_text("utf8") == md_content):
            # don't write if the content is the same
            # so that the file is not marked as changed by sphinx
            item_path.write_text(md_content)

        read_files.add(item_path.name)

    # road old files
    for item in current_files - read_files:
        roadmap_dir.joinpath(item).unlink()

import json
import os

import requests
import tomli
from dotenv import load_dotenv
from py_markdown_table.markdown_table import markdown_table
from rich.console import Console
from rich.table import Table

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_repositories_with_pyproject(username):
    # Define the GraphQL query
    query = """
        query($username: String!) {
            user(login: $username) {
                repositories(first: 100, ownerAffiliations: OWNER) {
                    nodes {
                        name
                        isFork
                        languages(first: 100) {
                            nodes {
                                name
                            }
                        }
                        object(expression: "main:pyproject.toml") {
                            ... on Blob {
                                isTruncated
                                text
                            }
                        }
                    }
                }
            }
        }
        """

    # Make the POST request to the GitHub GraphQL API
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": username}},
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    # Parse the response JSON
    data = json.loads(response.text)

    # Extract the repository names and file existence status
    repositories = []
    for repo in data["data"]["user"]["repositories"]["nodes"]:
        repo_name = repo["name"]
        languages = [lang["name"] for lang in repo["languages"]["nodes"]]
        if "Python" not in languages:
            continue
        if repo["isFork"]:
            continue
        file_exists = (
            True if repo["object"] and not repo["object"]["isTruncated"] else False
        )
        if file_exists:
            toml_text = repo["object"]["text"]
            toml_dict = tomli.loads(toml_text)
            python_version = (
                toml_dict.get("tool", {})
                .get("poetry", {})
                .get("dependencies", {})
                .get("python")
                .replace("^", "")
                .replace("~", "")
            )
        else:
            python_version = "N/A"
        repositories.append(
            {
                "name": repo_name,
                "file_exists": file_exists,
                "python_version": python_version,
            }
        )
        repositories = sorted(repositories, key=lambda x: x["name"])
        repositories = sorted(repositories, key=lambda x: x["python_version"])

    return repositories


# Call the function with the username 'oliveryh'
repositories = get_repositories_with_pyproject("oliveryh")

# Print the results
print(markdown_table(repositories).set_params(row_sep="markdown").get_markdown())

# Introduction

A tool to generate visualisations of the number of reviews being sent between contributors of GitHub repos. The success rate (ratio of approvals against change requests), is also indicated by the colour of the edges between nodes.

![Screenshot](https://github.com/oliveryh/toybox/blob/main/visualisations/github-reviews/screenshot.png)

# Installation

1. Clone this repo: `git clone git@github.com:oliveryh/toybox.git`
2. Enter the directory with this subproject
3. Create a python virtual environment `python3 -m venv venv`
4. Source the environment `source venv/bin/activate`

# Authentication

If you want to run the github visualisation against private repositories. You'll have to [create a personal access token for GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

# Usage

Once installed and authenticated, you can run `python generate_visualisation.py` and you'll be prompted to enter the owner and name of a github repository.

Here is an example using the django repository:

```
(venv) > python generate_visualisation.py --limit 1000
Your Repository Owner: django
Your Repository Name: django
ℹ️  - Requesting Data | owner: django | name: django
100%|█████████████████████████████████████████████████████████████████| 10/10 [00:11<00:00,  1.15s/it]
ℹ️  - You have 4990 credits left
✅ - Data generated
✅ - Database generated
✅ - Prepared connections from frontend
🌐 - Serving on http://localhost:8080
```

#!/usr/bin/env python
# coding: utf-8
import json
import os
from datetime import datetime

import notion
from notion.block import PageBlock
from notion.client import NotionClient
from notion.utils import now

token_v2 = "<redacted>"
BLOCK_URL = "<redacted>"


# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in session on Notion.so
client = NotionClient(token_v2=token_v2)

# Replace this URL with the URL of the page you want to edit
page = client.get_block(BLOCK_URL)

# Snippet of the format that we'll be saving the JSON in
#
# ``` json
# {
#     "name": "flare",
#     "children": [{
#         "name": "analytics",
#         "children": [{
#             "name": "cluster",
#             "children": [{
#                 "name": "AgglomerativeCluster",
#                 "size": 3938
#             }, {
#                 "name": "CommunityStructure",
#                 "size": 3812
#             }, {
#                 "name": "HierarchicalCluster",
#                 "size": 6714
#             }, {
#                 "name": "MergeEdge",
#                 "size": 743
#             }]
#         }, {
# ```


def get_page_age(page):
    last_edited_time = datetime.utcfromtimestamp(page.get("last_edited_time") / 1000)
    today = datetime.now()
    return (today - last_edited_time).days


def get_page_icon(page):
    uc = page.get("format.page_icon")
    if uc:
        return ord(uc[:1])
    else:
        return 0


def get_page_link(page):
    slug = page.title
    slug = slug.replace(" ", "-")
    slug = slug.replace(".", "-")
    hyperlink = (
        "https://www.notion.so/oliveryh/" + slug + "-" + page.id.replace("-", "")
    )
    return hyperlink


def get_tree(page, depth_limit=5):
    tree_struct = populate_children(page, depth_limit, 0)
    return tree_struct


def populate_children(page, depth_limit, depth):
    terminate = False
    if depth == depth_limit:
        terminate = True
    segment = {}
    segment["name"] = page.title
    segment["url"] = get_page_link(page)
    segment["age"] = get_page_age(page)
    segment["iconcode"] = get_page_icon(page)
    print(page.title)
    children = []
    for child in page.children:
        if isinstance(child, PageBlock):
            if terminate:
                children.append({"name": child.title})
            else:
                children.append(populate_children(child, depth_limit, depth + 1))
    if children:
        segment["children"] = children
    return segment


tree_struct = get_tree(page, 8)

with open("flare.json", "w") as f:
    json.dump(tree_struct, f)

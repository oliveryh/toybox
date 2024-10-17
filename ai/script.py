#!/usr/bin/env python
# coding: utf-8
import os

import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from tqdm import tqdm


from utils import scrub_email_addresses, scrub_names

OPENAI_KEY = os.getenv("OPENAI_KEY")

dataset = pd.read_csv("dataset.csv")
load_dotenv()
# Filter for conversation IDs from August 2023
conversation_ids = dataset[dataset["createdAt"].str.contains("2023-08")][
    "ConvID"
].unique()

conversation_ids_sample = conversation_ids[:10]

# Filter dataset if conversation ID is in August 2023
cleaned_dataset = dataset[dataset["ConvID"].isin(conversation_ids_sample)]
cleaned_dataset = cleaned_dataset[
    ["createdAt", "body_clean", "customer.id", "createdBy.id"]
]

tqdm.pandas()

# Apply the scrub functions to the body_clean column
cleaned_dataset["body_clean"] = cleaned_dataset["body_clean"].progress_apply(
    scrub_email_addresses
)
cleaned_dataset["body_clean"] = cleaned_dataset["body_clean"].progress_apply(
    scrub_names
)

prompt_template = """
You are an assistant to a team of customer service representatives. You have a series of emails in key and value pairs format.
You have been given the task of summarising the conversations in a paragraph of text.

Each email is separated by a "=============================" separator and looks like this:

createdAt: "2023-08-01T00:00:00.000Z"
customer.id: "12345"
body_clean": "This is the body of the email."

Here is the input for all the emails:

{email_json}

You can use the following template to help you write your summary:

Between the dates of X and Y, there were Z emails from our users. The emails were summarised as follows:

Formatted summary as a markdown list
"""

appends = []
for email in cleaned_dataset.to_dict(orient="records"):
    appends.append(
        """
    createdAt: {createdAt}
    customer.id: {customer_id}
    body_clean: {body_clean}
    """.format(
            createdAt=email["createdAt"],
            customer_id=email["customer.id"],
            body_clean=email["body_clean"],
        )
    )
    appends.append("=============================")

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["email_json"],
)

llm = ChatOpenAI(openai_api_key=OPENAI_KEY, model="gpt-4")
llm_chain = LLMChain(prompt=prompt, llm=llm, verbose=True)

response = llm_chain.run(
    {
        "email_json": "\n".join(appends),
    }
)

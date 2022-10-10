# Cyclexa bike journey duration prediction

## IInstallation

To run the notebook, please first create a virtual environment and then install the requirements file

`pip install -r requirements.txt`

## Creating a Report

1. Run the notebook with the log level set to WARN
2. Run the following command to generate a html file
   `jupyter nbconvert --to html --TemplateExporter.exclude_input=True --no-prompt --no-input report.ipynb --output report.html`

# Metis Data Science Bootcamp | Project 1
---

## Exploratory Data Analysis (EDA): NY Metro Transit Authority Turnstile Data

---
Project timeline: 4 days

**OUR TEAM**
- Elliot Wiens
- Wei Zhao
- Liam Isaacs

**BACK STORY**

WomenTechWomenYes (WTWY, a fictional organization) holds an annual gala at the beginning of each summer in New York City. To promote the Gala, WTWY will place street teams at entrances to subway stations. The street teams collect email addresses and those who sign up are sent free tickets to their gala (*View the full backstory [here](https://github.com/edubu2/metis-project1/blob/main/etc/project_background.md)*).

---
**OUR GOAL**

To use MTA subway data to help WTWY optimize the placement of their street teams such that they can gather the most signatures, ideally from those who will attend the gala and contribute to their cause.

---

**DELIVERABLES / PRESENTATION**

 * 8-10 minute group presentation in which all group members speak. This includes: 
   * slide presentation (final pdf version [here](https://github.com/edubu2/metis-project1/blob/main/etc/presentation_project1.pdf))
   * visual and oral communication in group presentations
   * organized project repository

---
#### **TECH STACK**

The following Python libraries were used to gather, clean, merge, analyze, and visualize the data:
- jupyter notebook
- pandas
- numpy
- pandas
- matplotlib
- seaborn
- google geocode API
- geopy
- geopandas
- json
- requests

---
#### **REQUIRED RESOURCES TO REPRODUCE LOCALLY**

- Python 3.x
- This Repository
  - Requires Git installation on your local machine and a GitHub account ([fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo) this repository and then [clone](https://docs.github.com/en/free-pro-team@latest/github/creating-cloning-and-archiving-repositories/cloning-a-repository) to your machine) 
- the above Python libraries (most of them included in anaconda distribution)
- Google ['Geocode' API](https://developers.google.com/maps/documentation/geocoding/start) key (in order to look up zipcode using latitude & longitude)
- jupyter notebook ([*what is jupyter?*](https://www.dataquest.io/blog/jupyter-notebook-tutorial/)) (also built-in with anaconda)
- the US Census data file called '18zpallagi.csv' that can be downloaded directly [here](https://www.irs.gov/downloads/irs-soi?C=M%3BO%3DD&sort=desc&order=Ng%C3%A0y&page=3) 
  - this is not included in the repository, as it is too large.
  - the other necessary data files are in the [/code/data folder](https://github.com/edubu2/metis-project1/tree/main/code/data)


#### **NAVIGATING THIS REPOSITORY**

Our code for gathering, cleaning and merging the data can be found in [/code/clean2.py](https://github.com/edubu2/metis-project1/blob/main/code/clean2.py)
  - the code in ``clean2.py`` was generated using jupyter notebook files.
  - our methods of creating this code is retained in [wtwy_data_merge.ipynb](https://github.com/edubu2/metis-project1/blob/main/code/wtwy_data_merge.ipynb)
  - clean2.py takes a couple of minutes to run due to the sheer size of the data (millions of rows being pulled and cleaned) as well as pulling zipcode data from geocode API
  - to better understand how to use clean2.py in jupyter notebook, see [``fresh_start.ipynb``](https://github.com/edubu2/metis-project1/blob/main/code/fresh_start.ipynb)
    - note that you will not be able to work on this file in your browser. To try it on your own, you will need to fork the repository, clone it to your machine, and open it with JupyterLab/Jupyter notebook

### Our Analysis & Conclusions

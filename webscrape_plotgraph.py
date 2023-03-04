# Web Scraping Refrences
# https://scrapfly.io/blog/web-scraping-with-selenium-and-python/#installing-selenium
# https://pythoninoffice.com/fixing-attributeerror-webdriver-object-has-no-attribute-find_element_by_xpath/
# https://www.guru99.com/accessing-forms-in-webdriver.html

# Graph Network & Plotting References
# https://towardsdatascience.com/customizing-networkx-graphs-f80b4e69bedf
# https://networkx.org/documentation/stable/reference/drawing.html

# Imports
from selenium import webdriver
from selenium.webdriver.common.by import By
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import re
import time

# Use FireFox
browser = webdriver.Firefox()
# URL Entrypoint
base_url = 'https://firststop.sos.nd.gov/search/business'
# Retrieve base page
browser.get(base_url)
# Find input box
browser.find_element(By.CLASS_NAME, 'search-input').send_keys("X")
# Find button for advanced options
browser.find_element(By.CLASS_NAME, 'advanced-search-toggle').click()
# Get radio buttons under advanced options
radio_buttons = browser.find_elements(By.XPATH, "//label[@class='field-label radio-label']")
# Click radio button for "Starts with" option (last radio button in list)
radio_buttons[-1].click()
# Click checkbox button for "Active entities only" option
browser.find_element(By.CLASS_NAME, 'checkbox-box').click()
# Click "Search" button
browser.find_element(By.XPATH,
    "//button[@class='btn btn-primary btn-raised advanced-search-button']").click()
# Allow company results to load on page
time.sleep(3)
# Capture each company button to click for more details
company_buttons = browser.find_elements(By.XPATH, "//div[@class='interactive-cell-button']")
# Store data output
df = pd.DataFrame(columns=['business','b_type','agent_owner','ao_type'])
# Visit all companies
for btn in company_buttons:
    # Click company button to load more details
    btn.click()
    # Allow company results to load on page
    time.sleep(3)
    # Filter for companies that start with "X"
    if btn.text.startswith("X"):
        # Extract company name and type
        business_name, business_type = btn.text.split('\n')
        # Extract table containing details
        company_details = browser.find_elements(By.XPATH,
            "//table[@class='details-list container-fluid']//tr[@class='detail ']")
        # Filter desired details about company
        for row in company_details:
            if re.search('Owners|Owner Name|Agent', row.text):
                # Extract owner or agent information
                owner_agent_type = row.find_element(By.CLASS_NAME, 'label').text
                owner_agent, *_ = row.find_element(By.CLASS_NAME, 'value').text.split('\n')
                # Save company details to output results
                df.loc[len(df.index)] = [business_name, business_type,
                                        owner_agent, owner_agent_type]
    # Reference: https://www.delftstack.com/howto/python/selenium-scroll-down-python/
    # Scroll so buttons come into view (and become click-able)
    browser.execute_script("window.scrollBy(0, 60);")
# Write data to CSV
df.to_csv('north_dakota_business.csv', index=False)
# Add categorical colors for business and agent type
df['b_color'] = df['b_type'].map({k:v for (k,v) in zip(df['b_type'].unique(),
                    plt.rcParams['axes.prop_cycle'].by_key()['color'])})
df['ao_color'] = df['ao_type'].map({k:v for (k,v) in zip(df['ao_type'].unique(),
                    ['gainsboro', 'dimgray', 'darkgray', 'whitesmoke'])})
# Add agent cardinality to filter for informational networks
df = df.join(df.groupby('agent_owner').apply(lambda df: df['business'].count()
            ).rename('cardinality').to_frame(), on='agent_owner')
# Configure plot
plt.figure(figsize=(5,5))
plt.title('North Dakota Corporations with Owners/Agent')
plt.axis('off')
# Create network graph
G = nx.from_pandas_edgelist(df, 'business', 'agent_owner')
# Configure cluster style
network_style = nx.spring_layout(G)
# Draw agent nodes - stylized
nx.draw_networkx_nodes(G, network_style,
    nodelist=list(df['agent_owner']),
    node_color=list(df['ao_color']),
    node_size=list(df['agent_owner'].apply(lambda x : G.degree(x)*20)),
    label='Agent/Owner')
# Draw business nodes - stylized
nx.draw_networkx_nodes(G, network_style,
    nodelist=list(df['business']),
    node_color=list(df['b_color']),
    node_size=20,
    node_shape='*',
    label='Business')
# Draw edges between nodes
nx.draw_networkx_edges(G, network_style)
# Label agents that have +1 connections
nx.draw_networkx_labels(G, network_style,
    labels={k:v for (k,v) in zip(df[df['cardinality'] > 1]['agent_owner'],
                                df[df['cardinality'] > 1]['agent_owner'])},
    font_size=5,
    horizontalalignment='left',
    verticalalignment='top',
    font_weight='bold')
# Display graph network
plt.legend()
plt.show()

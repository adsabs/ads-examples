"""
Simple example of how to plot metrics using Pandas
"""
import pandas as pd
import ads.sandbox as ads
import matplotlib.pyplot as plt
import seaborn

q = ads.SearchQuery(q='star')
q.execute()
df = pd.DataFrame.from_dict(q.response.json['response']['docs'])
print(df)

df['year'] = pd.to_numeric(df['year'], errors='ignore')
df['year'].plot.hist()
plt.savefig('example.jpg')

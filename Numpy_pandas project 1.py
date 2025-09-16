import numpy as np
import pandas as pd

df = pd.read_csv('/Users/karthikeyavaibhav/Desktop/Machine learning series/sample sets/Sample data sets/employee_dataset_with_duplicates.csv')
print(df)
#replace infinite and negative infinte values with null values
df.replace([np.inf, -np.inf], np.nan, inplace=True)

#handle negative values in the column and replace it with average value
df['Salary'] = np.where( df['Salary'] < 0, df['Salary'].mean(),df['Salary'])
df['Performance_Rating'] = np.where( df['Performance_Rating'] < 0, df['Performance_Rating'].mean(),df['Performance_Rating'])

#replaces null values with average values
df.fillna( df.mean(numeric_only=True), inplace=True )

#removes duplicate values if any
df.drop_duplicates(inplace=True)

print('Cleaned data')
print(df)


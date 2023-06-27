# Authors: Marcel Gunadi, Trien Bang Huynh and Minh Duc Vo

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np


'''
key:
l[0] = Year
l[1] = Rank
l[2] = Company
l[3] = Rev
l[4] = Profit
'''

data_names = ['Year', 'Rank', 'Company', 'Revenue', 'Profit']

import sqlite3
db = sqlite3.connect('lab.db')
cur = db.cursor()

# Validate shape of database table using dataframe
# cur.execute(f'''SELECT * FROM Lab JOIN {data_names[2]} ON Lab.{data_names[2]} = {data_names[2]}.id''')
# data_df = pd.DataFrame(cur.fetchall())

# print('The shape of the dataframe is:', data_df.shape) # tuple of (number of rows, number of columns)

cur.execute(f'''SELECT Lab.{data_names[0]}, Lab.{data_names[1]}, {data_names[2]}.{data_names[2]}, Lab.{data_names[3]}, Lab.{data_names[4]}  FROM Lab JOIN {data_names[2]}
                         ON Lab.{data_names[2]} = {data_names[2]}.id
                         WHERE Lab.{data_names[2]} >= 0 ''')


data_df = pd.DataFrame(cur.fetchall(), columns = ['Year', 'Rank', 'Company', 'Revenue', 'Profit'])


# --------------------------------PLOTINGS-----------------------------------
# Plotting Starts here
# Scatter plot

# Opition 1 - 1 Plot all data points by a year - plot 500 companies for the year we select
class Plotter:
  def by_year(self, year):
    # plt.figure()
    plt.scatter(data_df[data_df.Year == year].Revenue, data_df[data_df.Year == year].Profit)
    plt.title(f'Revenue vs Profit of fortune 500 companies for {year}')
    plt.xlabel('Revenue ($billions)')
    plt.ylabel('Profit ($billions)')
    # plt.show()

    # by_year(1995)

  # Option 1 - 2 Plot all data points for from a year to a year

  def year_to_year(self, startYear, endYear):
    # plt.figure(figsize=(10, 10))
    plt.title(f'Revenue vs Profit of fortune 500 companies from {startYear} to {endYear}')
    plt.xlabel('Revenue ($billions)')
    plt.ylabel('Profit ($billions)')

    for year in range(startYear, endYear + 1):
      plt.scatter(data_df[data_df.Year == year].Revenue, data_df[data_df.Year == year].Profit, label = year)
    plt.legend()
    # plt.show()

  # option 2
  def compare_companies_by_revenue(self, companyList):
    plt.title('Comparison of selected companies')
    plt.xlabel('Year')
    plt.ylabel('Revenue ($billions)')
    for company in companyList:
      plt.plot(data_df[data_df.Company == company].Year, data_df[data_df.Company == company].Revenue, label = company)
    plt.legend()
    # plt.show()

  def compare_companies_by_profit(self, companyList):
    plt.title('Comparison of selected companies')
    plt.xlabel('Year')
    plt.ylabel('Profit ($billions)')
    for company in companyList:
      plt.plot(data_df[data_df.Company == company].Year, data_df[data_df.Company == company].Profit, label = company)
    plt.legend()
    # plt.show()

    # year_to_year(1955, 1988)
    # year_to_year(1955, 2022)
    # compare_companies_by_revenue(['general motors', 'exxon mobil', 'u.s. steel'])
    # compare_companies_by_profit(['general sotors', 'exxon mobil', 'u.s. steel']) # Notice how U.S Steel only on top 500 for a while

  # New Line Plot - by rank
  def revenue_compare_nth_rank_companies(self, rank):
    nth_rank = data_df[data_df.Rank == rank]
    # plt.figure()
    plt.title(f'Revenue comparison of all rank {rank} companies from 1955 - 2022')
    plt.xlabel('Year')
    plt.ylabel('Revenue ($billions)')
    plt.plot(nth_rank.Year, nth_rank.Revenue)
    # plt.show()

  def profit_compare_nth_rank_companies(self, rank):
    nth_rank = data_df[data_df.Rank == rank]

    # plt.figure()
    plt.title(f'Profit comparison of all rank {rank} companies from 1955 - 2022')
    plt.xlabel('Year')
    plt.ylabel('Profit ($billions)')
    plt.plot(nth_rank.Year, nth_rank.Profit)
    # plt.show()

    # revenue_compare_nth_rank_companies(500)
    # profit_compare_nth_rank_companies(500)

  def train_model(self, X, y, degree):
      # Create polynomial features
      poly = PolynomialFeatures(degree=degree)
      X_poly = poly.fit_transform(X)

      # Train the model
      model = LinearRegression().fit(X_poly, y)

      # Generate new X values for the prediction range
      X_future = np.arange(1955, 2030).reshape(-1, 1)
      X_future_poly = poly.transform(X_future)

      # Predict
      y_pred_future = model.predict(X_future_poly)

      return X_future, y_pred_future

  def plot_prediction(self, X, y, X_future, y_pred_future, company, degree, label):
      # Plot
      # plt.figure(figsize=(10, 8))
      plt.scatter(X, y, color='blue', label=f'Actual {label}')
      plt.plot(X_future, y_pred_future, color='red', label=f'Predicted {label} ')
      plt.title(f'Future {label} Predictions for {company} (Polynomial Degree {degree})')
      plt.xlabel('Year')
      plt.ylabel(f'{label} ($billions)')
      plt.legend()
      # plt.show()

  def predict_company_revenue(self, company, degree):
      # Extract data for the given company
      company_df = data_df[data_df['Company'] == company]

      # Check if there is data for this company
      if company_df.empty:
          print(f"No data available for company: {company}")
          return

      # Define X (Year) and y for revenue
      X = company_df['Year'].values.reshape(-1,1)
      y_rev = company_df['Revenue'].values

      # Train the model and predict
      X_future, y_rev_pred_future = self.train_model(X, y_rev, degree)

      # Plot the prediction
      self.plot_prediction(X, y_rev, X_future, y_rev_pred_future, company, degree, 'Revenue')

  def predict_company_profit(self,company, degree):
      # Extract data for the given company
      company_df = data_df[data_df['Company'] == company]

      # Check if there is data for this company
      if company_df.empty:
          print(f"No data available for company: {company}")
          return

      # Define X (Year) and y for profit
      X = company_df['Year'].values.reshape(-1,1)
      y_prof = company_df['Profit'].values

      # Train the model and predict
      X_future, y_prof_pred_future = self.train_model(X, y_prof, degree)

      # Plot the prediction
      self.plot_prediction(X, y_prof, X_future, y_prof_pred_future, company, degree, 'Profit')






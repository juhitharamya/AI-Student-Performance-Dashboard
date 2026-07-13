"""Custom Machine Learning Package.

Exposes custom implementations of:
  • KMeans: Clustering algorithm for student performance grouping.
  • LinearRegression: Ordinary Least Squares algorithm for score prediction.
  • LogisticRegression: Sigmoid-based gradient descent for pass/fail probability.
"""

from .kmeans import KMeans
from .linear_regression import LinearRegression
from .logistic_regression import LogisticRegression

__all__ = ["KMeans", "LinearRegression", "LogisticRegression"]

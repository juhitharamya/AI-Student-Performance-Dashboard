"""Custom Linear Regression implementation using Ordinary Least Squares (OLS).

Mathematical Concept:
1. Hypothesis:
   y_pred = X * w + b
   We can rewrite this by appending a column of 1s to the feature matrix X (called the bias column) 
   and combining weights w and bias b into a single parameter vector W:
   y_pred = X_aug * W, where X_aug = [1 | X] and W = [b | w]^T

2. Loss function (Sum of Squared Errors):
   J(W) = sum( (y_pred_i - y_i)^2 ) = ||X_aug * W - y||^2

3. Optimization (Normal Equation):
   To minimize J(W), we take the derivative with respect to W and set it to 0:
   d/dW J(W) = 2 * X_aug^T * (X_aug * W - y) = 0
   X_aug^T * X_aug * W = X_aug^T * y
   W = (X_aug^T * X_aug)^(-1) * X_aug^T * y

4. Singular Matrix Handling:
   We use the Moore-Penrose pseudo-inverse (pinv) to compute (X_aug^T * X_aug)^(-1), 
   which remains stable even if feature columns are highly correlated (collinear) or 
   if there are fewer samples than features.
"""

import numpy as np

class LinearRegression:
    def __init__(self):
        self.coef_ = None  # Augment coefficients: [intercept, weight_1, weight_2, ...]
        self.intercept_ = 0.0
        self.weights_ = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearRegression":
        """Fit linear regression coefficients using the Normal Equation."""
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float).flatten()
        n_samples = X.shape[0]

        if n_samples == 0:
            return self

        # Step 1: Augment feature matrix with a bias column of ones
        X_aug = np.hstack([np.ones((n_samples, 1)), X])

        # Step 2: Compute W using the Normal Equation closed-form solution:
        # W = pinv(X_aug.T @ X_aug) @ X_aug.T @ y
        X_T_X = X_aug.T @ X_aug
        X_T_y = X_aug.T @ y
        
        # pinv (pseudo-inverse) uses Singular Value Decomposition (SVD) for absolute numerical stability
        self.coef_ = np.linalg.pinv(X_T_X) @ X_T_y

        self.intercept_ = float(self.coef_[0])
        self.weights_ = self.coef_[1:]

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict target values for input features X."""
        X = np.array(X, dtype=float)
        n_samples = X.shape[0]

        # Augment input feature matrix with bias column
        X_aug = np.hstack([np.ones((n_samples, 1)), X])

        # y_pred = X_aug @ W
        return np.dot(X_aug, self.coef_)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate the R^2 coefficient of determination."""
        y_pred = self.predict(X)
        y_true = np.array(y, dtype=float).flatten()
        u = np.sum((y_true - y_pred) ** 2)
        v = np.sum((y_true - np.mean(y_true)) ** 2)
        if v == 0:
            return 0.0
        return float(1.0 - (u / v))

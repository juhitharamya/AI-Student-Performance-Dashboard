"""Custom Logistic Regression implementation using Gradient Descent.

Mathematical Concept:
1. Hypothesis (Sigmoid function):
   z = X * w + b
   p = sigma(z) = 1 / (1 + exp(-z))
   where p is the probability of class 1 (e.g., student passing).

2. Loss function (Binary Cross Entropy):
   J(w, b) = -1/M * sum( y_i * log(p_i) + (1 - y_i) * log(1 - p_i) )

3. Gradient Calculations:
   dw = 1/M * X^T * (p - y)
   db = 1/M * sum(p - y)

4. Gradient Descent Optimization:
   w = w - learning_rate * dw
   b = b - learning_rate * db

5. Feature Scaling (Standardization):
   Since grade scores usually range between 0 and 100, we apply Z-score normalization 
   internally: X_scaled = (X - mean) / stdev. This prevents gradient explosion and 
   ensures faster convergence.
"""

import numpy as np

class LogisticRegression:
    def __init__(self, learning_rate: float = 0.05, max_iter: int = 1000, tol: float = 1e-4):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.tol = tol
        
        self.weights = None
        self.intercept = 0.0
        
        # Internal normalization parameters
        self.mean = None
        self.stdev = None

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        # Clip to prevent overflow/underflow in exp(-z)
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegression":
        """Train weights and bias using gradient descent on Binary Cross Entropy Loss."""
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float).flatten()
        n_samples, n_features = X.shape

        if n_samples == 0:
            return self

        # Step 1: Standardize features for gradient descent stability
        self.mean = np.mean(X, axis=0)
        self.stdev = np.std(X, axis=0)
        # Avoid division by zero
        self.stdev[self.stdev == 0] = 1.0
        X_scaled = (X - self.mean) / self.stdev

        # Step 2: Initialize weights and bias
        self.weights = np.zeros(n_features)
        self.intercept = 0.0

        for iteration in range(self.max_iter):
            # Forward pass: compute probabilities
            z = np.dot(X_scaled, self.weights) + self.intercept
            p = self._sigmoid(z)

            # Clip probabilities to avoid log(0)
            p = np.clip(p, 1e-15, 1 - 1e-15)

            # Step 3: Gradient calculations
            dw = (1.0 / n_samples) * np.dot(X_scaled.T, (p - y))
            db = (1.0 / n_samples) * np.sum(p - y)

            # Keep track of previous parameters for convergence check
            prev_weights = self.weights.copy()
            prev_intercept = self.intercept

            # Step 4: Gradient Descent Updates
            self.weights -= self.learning_rate * dw
            self.intercept -= self.learning_rate * db

            # Step 5: Check convergence
            weight_shift = np.sum(np.abs(self.weights - prev_weights))
            bias_shift = np.abs(self.intercept - prev_intercept)
            if (weight_shift + bias_shift) < self.tol:
                break

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Calculate pass probabilities (class 1)."""
        X = np.array(X, dtype=float)
        # Scale features using the mean/stdev computed during training
        X_scaled = (X - self.mean) / self.stdev
        z = np.dot(X_scaled, self.weights) + self.intercept
        return self._sigmoid(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary class (0 or 1) based on a 0.5 probability threshold."""
        prob = self.predict_proba(X)
        return (prob >= 0.5).astype(int)

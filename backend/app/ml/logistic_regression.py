"""Custom Logistic Regression implementation in pure Python.

Uses Gradient Descent with Binary Cross Entropy Loss and standardizes features internally.
"""

import math

class LogisticRegression:
    def __init__(self, learning_rate: float = 0.05, max_iter: int = 1000, tol: float = 1e-4):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.tol = tol
        
        self.weights = None  # list of weights
        self.intercept = 0.0
        
        # Normalization parameters
        self.mean = None
        self.stdev = None

    def _sigmoid(self, z: float) -> float:
        # Clip to prevent overflow/underflow
        z = max(-500.0, min(500.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    def fit(self, X, y) -> "LogisticRegression":
        """Train weights and bias using gradient descent on Binary Cross Entropy Loss."""
        if X is None or len(X) == 0:
            return self

        # Convert to list of lists of floats
        first_el = X[0]
        if isinstance(first_el, (int, float)):
            data = [[float(x)] for x in X]
        else:
            data = [[float(v) for v in row] for row in X]

        targets = [float(v) for v in y]
        n_samples = len(data)
        n_features = len(data[0])

        # Step 1: Standardize features for gradient descent stability
        self.mean = [0.0] * n_features
        self.stdev = [0.0] * n_features

        for f in range(n_features):
            col = [row[f] for row in data]
            col_mean = sum(col) / n_samples
            self.mean[f] = col_mean
            
            variance = sum((x - col_mean) ** 2 for x in col) / n_samples
            self.stdev[f] = math.sqrt(variance)
            if self.stdev[f] == 0.0:
                self.stdev[f] = 1.0

        X_scaled = []
        for row in data:
            scaled_row = [(row[f] - self.mean[f]) / self.stdev[f] for f in range(n_features)]
            X_scaled.append(scaled_row)

        # Step 2: Initialize weights and bias
        self.weights = [0.0] * n_features
        self.intercept = 0.0

        for iteration in range(self.max_iter):
            # Forward pass: compute probabilities
            probs = []
            for row in X_scaled:
                z = sum(row[f] * self.weights[f] for f in range(n_features)) + self.intercept
                p = self._sigmoid(z)
                p = max(1e-15, min(1.0 - 1e-15, p))  # Clip to prevent log(0)
                probs.append(p)

            # Step 3: Gradient calculations
            dw = [0.0] * n_features
            db = 0.0
            for i in range(n_samples):
                diff = probs[i] - targets[i]
                for f in range(n_features):
                    dw[f] += X_scaled[i][f] * diff
                db += diff

            for f in range(n_features):
                dw[f] /= n_samples
            db /= n_samples

            # Keep track of previous parameters for convergence check
            prev_weights = list(self.weights)
            prev_intercept = self.intercept

            # Step 4: Gradient Descent Updates
            for f in range(n_features):
                self.weights[f] -= self.learning_rate * dw[f]
            self.intercept -= self.learning_rate * db

            # Step 5: Check convergence
            weight_shift = sum(abs(self.weights[f] - prev_weights[f]) for f in range(n_features))
            bias_shift = abs(self.intercept - prev_intercept)
            if (weight_shift + bias_shift) < self.tol:
                break

        return self

    def predict_proba(self, X) -> list[float]:
        """Calculate pass probabilities (class 1)."""
        if not self.weights or X is None or len(X) == 0:
            return []

        first_el = X[0]
        if isinstance(first_el, (int, float)):
            data = [[float(x)] for x in X]
        else:
            data = [[float(v) for v in row] for row in X]

        n_features = len(data[0])
        probs = []
        for row in data:
            scaled_row = [(row[f] - self.mean[f]) / self.stdev[f] for f in range(n_features)]
            z = sum(scaled_row[f] * self.weights[f] for f in range(n_features)) + self.intercept
            probs.append(self._sigmoid(z))
        return probs

    def predict(self, X) -> list[int]:
        """Predict binary class (0 or 1) based on a 0.5 probability threshold."""
        prob = self.predict_proba(X)
        return [1 if p >= 0.5 else 0 for p in prob]

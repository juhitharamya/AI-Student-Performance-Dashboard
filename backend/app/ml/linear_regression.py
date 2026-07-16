"""Custom Linear Regression implementation in pure Python.

Uses Ordinary Least Squares (OLS) with Ridge L2 regularization for absolute numerical stability.
"""

class LinearRegression:
    def __init__(self):
        self.coef_ = None  # Augment coefficients: [intercept, weight_1, weight_2, ...]
        self.intercept_ = 0.0
        self.weights_ = None

    def fit(self, X, y) -> "LinearRegression":
        """Fit linear regression coefficients using the Normal Equation."""
        if X is None or len(X) == 0:
            return self

        data = [[float(v) for v in row] for row in X]
        targets = [float(v) for v in y]
        n_samples = len(data)

        # Step 1: Augment feature matrix with a bias column of ones
        X_aug = [[1.0] + row for row in data]
        n_features_aug = len(X_aug[0])

        # Step 2: Compute W using the Normal Equation closed-form solution:
        # W = inv(X_aug.T @ X_aug) @ X_aug.T @ y
        
        # Compute X_T (transpose of X_aug)
        X_T = [list(x) for x in zip(*X_aug)]

        # Compute X_T_X = X_T @ X_aug
        X_T_X = [[0.0] * n_features_aug for _ in range(n_features_aug)]
        for i in range(n_features_aug):
            for j in range(n_features_aug):
                X_T_X[i][j] = sum(X_T[i][k] * X_aug[k][j] for k in range(n_samples))

        # Add small L2 regularization (Ridge penalty) to diagonal for absolute stability
        lambda_reg = 1e-4
        for i in range(n_features_aug):
            X_T_X[i][i] += lambda_reg

        # Compute X_T_y = X_T @ y
        X_T_y = [0.0] * n_features_aug
        for i in range(n_features_aug):
            X_T_y[i] = sum(X_T[i][k] * targets[k] for k in range(n_samples))

        # Solve for coefficients W = (X_T_X)^-1 @ X_T_y
        try:
            inv_X_T_X = self._invert_matrix(X_T_X)
            self.coef_ = [sum(inv_X_T_X[i][j] * X_T_y[j] for j in range(n_features_aug)) for i in range(n_features_aug)]
        except ValueError:
            # Fallback to mean predictor if matrix inversion fails
            mean_y = sum(targets) / n_samples
            self.coef_ = [mean_y] + [0.0] * (n_features_aug - 1)

        self.intercept_ = float(self.coef_[0])
        self.weights_ = self.coef_[1:]

        return self

    def _invert_matrix(self, A):
        """Invert N x N matrix A using Gauss-Jordan elimination with partial pivoting."""
        n = len(A)
        aug = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
        
        for i in range(n):
            # Pivot selection
            pivot_row = i
            for r in range(i + 1, n):
                if abs(aug[r][i]) > abs(aug[pivot_row][i]):
                    pivot_row = r
            if pivot_row != i:
                aug[i], aug[pivot_row] = aug[pivot_row], aug[i]
            
            pivot = aug[i][i]
            if abs(pivot) < 1e-12:
                raise ValueError("Singular matrix")
                
            # Normalize pivot row
            for c in range(i, 2 * n):
                aug[i][c] /= pivot
                
            # Eliminate columns
            for r in range(n):
                if r != i:
                    factor = aug[r][i]
                    for c in range(i, 2 * n):
                        aug[r][c] -= factor * aug[i][c]
                        
        inv = [row[n:] for row in aug]
        return inv

    def predict(self, X) -> list[float]:
        """Predict target values for input features X."""
        if not self.coef_ or X is None or len(X) == 0:
            return []

        data = [[float(v) for v in row] for row in X]
        preds = []
        for row in data:
            pred = self.intercept_ + sum(row[f] * self.weights_[f] for f in range(len(row)))
            preds.append(pred)
        return preds

    def score(self, X, y) -> float:
        """Calculate the R^2 coefficient of determination."""
        y_pred = self.predict(X)
        y_true = [float(v) for v in y]
        n_samples = len(y_true)
        if n_samples == 0:
            return 0.0
            
        mean_y = sum(y_true) / n_samples
        u = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n_samples))
        v = sum((y_true[i] - mean_y) ** 2 for i in range(n_samples))
        if v == 0.0:
            return 0.0
        return float(1.0 - (u / v))

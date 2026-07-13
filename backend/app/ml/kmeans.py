"""Custom K-Means Clustering implementation.

Mathematical Concept:
1. Centroids Initialization: Initialize K centroids (either randomly or spaced out).
2. Assignment Step: Assign each data point to its closest centroid using Euclidean distance:
   d(x, c) = sqrt( sum( (x_i - c_i)^2 ) )
3. Update Step: Calculate the new centroids as the mean of all data points assigned to each cluster:
   c_k = (1 / |S_k|) * sum(x) for all x in S_k
4. Convergence Check: Repeat steps 2 and 3 until centroids stabilize or max iterations are reached.
"""

import numpy as np

class KMeans:
    def __init__(self, n_clusters: int = 4, max_iter: int = 100, tol: float = 1e-4):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None

    def fit(self, X: np.ndarray) -> "KMeans":
        """Fit the model to dataset X of shape (n_samples, n_features)."""
        X = np.array(X, dtype=float)
        n_samples, n_features = X.shape

        if n_samples == 0:
            return self

        # Adjust clusters if sample size is smaller than desired clusters
        actual_k = min(self.n_clusters, n_samples)

        # Step 1: Initialize Centroids
        # We sort samples along the first axis and pick evenly-spaced initial centroids.
        # This is extremely stable for student grade analysis (e.g., low, medium, high boundaries).
        sorted_indices = np.argsort(X[:, 0])
        indices = np.linspace(0, n_samples - 1, actual_k, dtype=int)
        centroids = X[sorted_indices[indices]].copy()

        for iteration in range(self.max_iter):
            # Step 2: Assignment Step
            # Calculate distance from each sample to each centroid
            # distances shape: (n_samples, actual_k)
            distances = np.zeros((n_samples, actual_k))
            for k in range(actual_k):
                # Euclidean distance: sqrt(sum((x - c)^2))
                diff = X - centroids[k]
                distances[:, k] = np.sqrt(np.sum(diff ** 2, axis=1))

            # Assign each sample to the nearest centroid index
            labels = np.argmin(distances, axis=1)

            # Step 3: Update Step
            new_centroids = np.zeros_like(centroids)
            for k in range(actual_k):
                # Find all samples assigned to cluster k
                members = X[labels == k]
                if len(members) > 0:
                    # New centroid is the arithmetic mean of its members
                    new_centroids[k] = np.mean(members, axis=0)
                else:
                    # If empty, keep previous centroid
                    new_centroids[k] = centroids[k]

            # Step 4: Convergence Check
            # Check if centroids shifted by less than tolerance
            shift = np.sum(np.abs(new_centroids - centroids))
            if shift < self.tol:
                centroids = new_centroids
                break

            centroids = new_centroids

        self.cluster_centers_ = centroids
        
        # Compute final assignments and inertia (sum of squared distances to closest centroid)
        final_distances = np.zeros((n_samples, actual_k))
        for k in range(actual_k):
            final_distances[:, k] = np.sum((X - centroids[k]) ** 2, axis=1)
        
        self.labels_ = np.argmin(final_distances, axis=1)
        self.inertia_ = float(np.sum(np.min(final_distances, axis=1)))

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Assign new samples in X to the closest centroid."""
        X = np.array(X, dtype=float)
        n_samples = X.shape[0]
        actual_k = len(self.cluster_centers_)

        distances = np.zeros((n_samples, actual_k))
        for k in range(actual_k):
            diff = X - self.cluster_centers_[k]
            distances[:, k] = np.sqrt(np.sum(diff ** 2, axis=1))

        return np.argmin(distances, axis=1)

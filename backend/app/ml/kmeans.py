"""Custom K-Means Clustering implementation in pure Python.

Mathematical Concept:
1. Centroids Initialization: Initialize K centroids by picking evenly-spaced points along the first axis after sorting.
2. Assignment Step: Assign each data point to its closest centroid using Euclidean distance.
3. Update Step: Calculate the new centroids as the mean of all data points assigned to each cluster.
4. Convergence Check: Repeat steps 2 and 3 until centroids stabilize or max iterations are reached.
"""

import math

class KMeans:
    def __init__(self, n_clusters: int = 4, max_iter: int = 100, tol: float = 1e-4):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None

    def fit(self, X) -> "KMeans":
        """Fit the model to dataset X of shape (n_samples, n_features)."""
        if X is None or len(X) == 0:
            self.cluster_centers_ = []
            self.labels_ = []
            self.inertia_ = 0.0
            return self

        # Convert to list of lists of floats
        first_el = X[0]
        if isinstance(first_el, (int, float)):
            data = [[float(x)] for x in X]
        else:
            data = [[float(v) for v in row] for row in X]

        n_samples = len(data)
        n_features = len(data[0])
        actual_k = min(self.n_clusters, n_samples)

        # Step 1: Initialize Centroids
        # Sort samples along the first axis and pick evenly-spaced initial centroids
        sorted_indices = sorted(range(n_samples), key=lambda i: data[i][0])
        
        if actual_k > 1:
            indices = [int(i * (n_samples - 1) / (actual_k - 1)) for i in range(actual_k)]
        else:
            indices = [0]
            
        centroids = [list(data[sorted_indices[idx]]) for idx in indices]

        for iteration in range(self.max_iter):
            # Step 2: Assignment Step
            labels = []
            for row in data:
                min_dist = float('inf')
                best_k = 0
                for k in range(actual_k):
                    # Euclidean distance: sqrt(sum((x - c)^2))
                    dist = math.sqrt(sum((row[f] - centroids[k][f]) ** 2 for f in range(n_features)))
                    if dist < min_dist:
                        min_dist = dist
                        best_k = k
                labels.append(best_k)

            # Step 3: Update Step
            new_centroids = [[0.0] * n_features for _ in range(actual_k)]
            counts = [0] * actual_k
            for i, row in enumerate(data):
                k = labels[i]
                for f in range(n_features):
                    new_centroids[k][f] += row[f]
                counts[k] += 1

            for k in range(actual_k):
                if counts[k] > 0:
                    for f in range(n_features):
                        new_centroids[k][f] /= counts[k]
                else:
                    new_centroids[k] = list(centroids[k])

            # Step 4: Convergence Check
            # Check if centroids shifted by less than tolerance
            shift = 0.0
            for k in range(actual_k):
                shift += sum(abs(new_centroids[k][f] - centroids[k][f]) for f in range(n_features))

            centroids = new_centroids
            if shift < self.tol:
                break

        self.cluster_centers_ = centroids
        self.labels_ = labels

        # Compute final inertia (sum of squared distances to closest centroid)
        inertia = 0.0
        for i, row in enumerate(data):
            k = labels[i]
            inertia += sum((row[f] - centroids[k][f]) ** 2 for f in range(n_features))
        self.inertia_ = inertia

        return self

    def predict(self, X):
        """Assign new samples in X to the closest centroid."""
        if not self.cluster_centers_ or X is None or len(X) == 0:
            return []

        first_el = X[0]
        if isinstance(first_el, (int, float)):
            data = [[float(x)] for x in X]
        else:
            data = [[float(v) for v in row] for row in X]

        n_features = len(data[0])
        actual_k = len(self.cluster_centers_)

        labels = []
        for row in data:
            min_dist = float('inf')
            best_k = 0
            for k in range(actual_k):
                dist = math.sqrt(sum((row[f] - self.cluster_centers_[k][f]) ** 2 for f in range(n_features)))
                if dist < min_dist:
                    min_dist = dist
                    best_k = k
            labels.append(best_k)

        return labels

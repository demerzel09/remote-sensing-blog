import numpy as np
from sklearn.ensemble import RandomForestClassifier


def train_model(features, labels, n_estimators=100, random_state=0):
    """Train a RandomForest model."""
    X = features.reshape(features.shape[0], -1).T
    y = labels.flatten()
    mask = ~np.isnan(X).any(axis=1)
    X = X[mask]
    y = y[mask]
    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
    clf.fit(X, y)
    return clf

import numpy as np
from sklearn.ensemble import RandomForestClassifier


def train_model(
    features,
    labels,
    n_estimators=100,
    random_state=0,
    max_depth=None,
    max_samples=None,
    verbose=0,
):
    """Train a RandomForest model.

    Parameters
    ----------
    features : np.ndarray
        Array of features with shape ``(bands, n_samples)`` or
        ``(bands, height, width)``.
    labels : np.ndarray
        Corresponding label raster or array.
    n_estimators : int, optional
        Number of trees in the forest.
    random_state : int, optional
        Seed for the ``RandomForestClassifier``.
    max_depth : int or None, optional
        Maximum depth of the trees.
    max_samples : int, float or None, optional
        Number or fraction of samples to draw for training each tree.
    verbose : int, optional
        Verbosity level for ``RandomForestClassifier``.
    """
    X = features.reshape(features.shape[0], -1).T
    y = labels.flatten()
    mask = ~np.isnan(X).any(axis=1)
    X = X[mask]
    y = y[mask]
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        max_depth=max_depth,
        max_samples=max_samples,
        verbose=verbose,
    )
    clf.fit(X, y)
    return clf

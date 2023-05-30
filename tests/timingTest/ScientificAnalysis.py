import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Generate random input data
num_samples = 500000
num_features = 10
data = np.random.rand(num_samples, num_features + 1)
data[:, -1] = np.round(data[:, -1])  # Set the last column to be binary labels (0 or 1)

# Save the data to a CSV file
df = pd.DataFrame(data, columns=['feat' + str(i+1) for i in range(num_features)] + ['label'])
df.to_csv('input_data.csv', index=False)

# Split the data into training and testing sets
train_data = df.sample(frac=0.8, random_state=1)
test_data = df.drop(train_data.index)

# Separate the labels from the features
train_labels = train_data.pop('label').values
test_labels = test_data.pop('label').values
train_features = train_data.values
test_features = test_data.values

# Train a k-random forest classifier on the training data
num_trees = 100
clf = RandomForestClassifier(n_estimators=num_trees, max_depth=None, random_state=1)
clf.fit(train_features, train_labels)

# Evaluate the classifier on the testing data
accuracy = clf.score(test_features, test_labels)
print("Accuracy:", accuracy)

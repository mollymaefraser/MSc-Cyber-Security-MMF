import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ---------------------------------------------------------
# 1. LOAD DATASET
# Problem: Classifying Iris flower species (setosa, versicolor, virginica)
# based on four features: sepal length, sepal width, petal length, and petal width.
# ---------------------------------------------------------

# Load the built-in Iris dataset (a standard public dataset)
iris = load_iris()
X = iris.data    # Features
y = iris.target  # Target variable (species 0, 1, 2)

# Convert to DataFrame for better inspection (optional but good practice)
df = pd.DataFrame(X, columns=iris.feature_names)
df['species'] = y

print("--- Data Inspection ---")
print(df.head())
print(f"\nTotal samples: {len(df)}")

# ---------------------------------------------------------
# 2. DATA SPLIT AND MODEL TRAINING
# ---------------------------------------------------------

# Split the data into training (80%) and testing (20%) sets
# random_state ensures reproducibility
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize the model: Logistic Regression is simple, robust, and interpretable
model = LogisticRegression(max_iter=200, random_state=42)

# Train the model using the training data
model.fit(X_train, y_train)
print("\nModel training complete.")

# ---------------------------------------------------------
# 3. PREDICTION AND EVALUATION
# ---------------------------------------------------------

# Make predictions on the test set
y_pred = model.predict(X_test)

print("\n--- Model Performance Evaluation ---")

# 1. Accuracy Score
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.4f} (Proportion of correct predictions)")

# 2. Confusion Matrix
# Shows where the model made mistakes (e.g., predicted species 1 when it was species 2)
cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix:")
print(cm)
# The ideal result is a diagonal matrix, showing all samples were correctly classified.

# 3. Classification Report (Detailed Metrics)
# Provides Precision, Recall, and F1-score for each class (species)
report = classification_report(y_test, y_pred, target_names=iris.target_names)
print("\nClassification Report:")
print(report)

# Interpretation:
# Precision: Out of all samples predicted for a class, how many were correct?
# Recall: Out of all true samples of a class, how many did the model find?
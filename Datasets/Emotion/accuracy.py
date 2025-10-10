import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from statsmodels.stats.contingency_tables import mcnemar

# ---------------- Load Dataset ----------------
df = pd.read_csv("Datasets/Emotion/train_converted.csv")
texts = df["text"].tolist()
labels = df["mood"].tolist()

# ---------------- Text Vectorization ----------------
vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
X = vectorizer.fit_transform(texts)
y = np.array(labels)

# ---------------- Model ----------------
model = LogisticRegression(max_iter=1000)

# ---------------- 1️⃣ Cross-Validation Performance ----------------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')

print("Cross-Validation Accuracies:", cv_scores)
print("Mean Accuracy:", cv_scores.mean())

# --- Plot Cross-Validation Performance ---
plt.figure(figsize=(7,5))
sns.barplot(x=[f"Fold {i+1}" for i in range(len(cv_scores))], y=cv_scores, palette="viridis")
plt.title("Cross-Validation Accuracy per Fold")
plt.ylabel("Accuracy")
plt.ylim(0.85, 1.0)
plt.axhline(cv_scores.mean(), color="red", linestyle="--", label=f"Mean: {cv_scores.mean():.3f}")
plt.legend()
plt.tight_layout()
plt.show()

# ---------------- 2️⃣ Statistical Tests ----------------
# Split for statistical evaluation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.8, random_state=42)

# Train two models to compare (for McNemar's)
model_A = LogisticRegression(max_iter=1000, random_state=42)
model_B = LogisticRegression(max_iter=1000, C=0.5, random_state=42)  # Slight variation

model_A.fit(X_train, y_train)
model_B.fit(X_train, y_train)

y_pred_A = model_A.predict(X_test)
y_pred_B = model_B.predict(X_test)

# --- Confusion Table for McNemar's test ---
tb = confusion_matrix(y_pred_A == y_test, y_pred_B == y_test)
print("\nMcNemar’s Test Contingency Table:")
print(tb)

# --- McNemar’s Test ---
result = mcnemar(tb, exact=True)
print(f"\nMcNemar’s Test Statistic: {result.statistic:.4f}, p-value: {result.pvalue:.4f}")

# --- Plot McNemar Contingency Table ---
plt.figure(figsize=(4,4))
sns.heatmap(tb, annot=True, fmt='d', cmap='coolwarm', cbar=False)
plt.title("McNemar’s Test Contingency Table")
plt.xlabel("Model B Agreement")
plt.ylabel("Model A Agreement")
plt.tight_layout()
plt.show()

# ---------------- 3️⃣ Cohen’s Kappa (Agreement) ----------------
kappa = cohen_kappa_score(y_pred_A, y_pred_B)
print(f"\nCohen’s Kappa: {kappa:.4f}")

# --- Plot Cohen’s Kappa as Gauge Chart ---
fig, ax = plt.subplots(figsize=(6, 2))
ax.barh(["Agreement"], [kappa], color="teal")
ax.set_xlim(0, 1)
ax.set_title("Cohen’s Kappa Agreement Level")
for i, v in enumerate([kappa]):
    ax.text(v + 0.02, i, f"{v:.2f}", color="black", va="center", fontweight="bold")
plt.tight_layout()
plt.show()

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_curve, auc
)
from sklearn.preprocessing import label_binarize
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.contingency_tables import mcnemar

# ---------------- Load Dataset ----------------
df = pd.read_csv("Datasets/Emotion/train_converted.csv")
texts = df["text"].tolist()
labels = df["mood"].tolist()
classes = sorted(df["mood"].unique())

# ---------------- Text Vectorization ----------------
vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
X = vectorizer.fit_transform(texts)
y = np.array(labels)

# ---------------- Base Model ----------------
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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.9, random_state=42)

model_A = LogisticRegression(max_iter=1000, random_state=42)
model_B = LogisticRegression(max_iter=1000, C=0.5, random_state=42)

model_A.fit(X_train, y_train)
model_B.fit(X_train, y_train)

y_pred_A = model_A.predict(X_test)
y_pred_B = model_B.predict(X_test)

tb = confusion_matrix(y_pred_A == y_test, y_pred_B == y_test)
print("\nMcNemar’s Test Contingency Table:")
print(tb)

result = mcnemar(tb, exact=True)
print(f"\nMcNemar’s Test Statistic: {result.statistic:.4f}, p-value: {result.pvalue:.4f}")

plt.figure(figsize=(4,4))
sns.heatmap(tb, annot=True, fmt='d', cmap='coolwarm', cbar=False)
plt.title("McNemar’s Test Contingency Table")
plt.xlabel("Model B Agreement")
plt.ylabel("Model A Agreement")
plt.tight_layout()
plt.show()

# ---------------- 3️⃣ Cohen’s Kappa ----------------
kappa = cohen_kappa_score(y_pred_A, y_pred_B)
print(f"\nCohen’s Kappa: {kappa:.4f}")

plt.figure(figsize=(6,2))
plt.barh(["Agreement"], [kappa], color="teal")
plt.xlim(0,1)
plt.title("Cohen’s Kappa Agreement Level")
plt.text(kappa + 0.02, 0, f"{kappa:.2f}", va="center")
plt.tight_layout()
plt.show()

# ---------------- 4️⃣ Final Evaluation ----------------

start_train = time.time()
model.fit(X, y)
training_time = time.time() - start_train

start_inf = time.time()
y_pred = model.predict(X)
inference_time = time.time() - start_inf

accuracy = accuracy_score(y, y_pred)
precision = precision_score(y, y_pred, average='weighted', zero_division=0)
recall = recall_score(y, y_pred, average='weighted', zero_division=0)
f1 = f1_score(y, y_pred, average='weighted', zero_division=0)

report = classification_report(y, y_pred, output_dict=True, zero_division=0)
report_df = pd.DataFrame(report).transpose()

cm = confusion_matrix(y, y_pred, labels=classes)

# ---------------- 5️⃣ Multi-Class ROC Curve ----------------
y_bin = label_binarize(y, classes=classes)
n_classes = len(classes)

y_prob = model.predict_proba(X)

fpr = {}
tpr = {}
roc_auc = {}

for i in range(n_classes):
    fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], y_prob[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

fpr["micro"], tpr["micro"], _ = roc_curve(y_bin.ravel(), y_prob.ravel())
roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))
mean_tpr = np.zeros_like(all_fpr)

for i in range(n_classes):
    mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])

mean_tpr /= n_classes

fpr["macro"] = all_fpr
tpr["macro"] = mean_tpr
roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

plt.figure(figsize=(10, 7))

plt.plot(fpr["micro"], tpr["micro"],
         label=f"Micro-average ROC (AUC = {roc_auc['micro']:.3f})",
         linewidth=2)

plt.plot(fpr["macro"], tpr["macro"],
         label=f"Macro-average ROC (AUC = {roc_auc['macro']:.3f})",
         linewidth=2)

for i in range(n_classes):
    plt.plot(fpr[i], tpr[i],
             label=f"{classes[i]} (AUC = {roc_auc[i]:.3f})",
             linestyle="--")

plt.plot([0, 1], [0, 1], "k--")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Multi-Class ROC Curve (One-vs-Rest)")
plt.legend(loc="lower right")
plt.tight_layout()
plt.show()

# ---------------- Tkinter GUI ----------------
root = tk.Tk()
root.title("Model Evaluation Dashboard")
root.geometry("1200x900")
root.configure(bg='white')

metrics_frame = tk.Frame(root, bg='white')
metrics_frame.pack(pady=10)

tk.Label(metrics_frame, text="Overall Model Performance", font=("Arial", 16, "bold"), bg='white').pack()

metrics_text = f"""
Training Time: {training_time:.4f} sec
Inference Time: {inference_time:.4f} sec
Accuracy: {accuracy:.4f}
Precision: {precision:.4f}
Recall: {recall:.4f}
F1-Score: {f1:.4f}
"""
tk.Label(metrics_frame, text=metrics_text, font=("Arial", 12), justify='left', bg='white').pack()

# ---------------- Charts ----------------
fig, axes = plt.subplots(2, 2, figsize=(12,10))
plt.subplots_adjust(hspace=0.4, wspace=0.3)

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes, ax=axes[0,0])
axes[0,0].set_title('Confusion Matrix')
axes[0,0].set_xlabel('Predicted')
axes[0,0].set_ylabel('Actual')

metrics_df = pd.DataFrame({
    'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
    'Score': [accuracy, precision, recall, f1]
})
sns.barplot(x='Metric', y='Score', data=metrics_df, palette='viridis', ax=axes[0,1])
axes[0,1].set_ylim(0,1)
axes[0,1].set_title('Overall Model Metrics')

class_metrics = report_df.loc[classes, ['precision','recall','f1-score']].reset_index().melt(id_vars='index')
sns.barplot(x='index', y='value', hue='variable', data=class_metrics, palette='Set2', ax=axes[1,0])
axes[1,0].set_ylim(0,1)
axes[1,0].set_xlabel('Class')
axes[1,0].set_ylabel('Score')
axes[1,0].set_title('Class-wise Metrics')

sns.countplot(x=labels, palette='pastel', ax=axes[1,1])
axes[1,1].set_title('Actual Class Distribution')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(pady=10)

root.mainloop()

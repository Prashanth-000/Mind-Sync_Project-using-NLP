import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# ---------------- Load Data ----------------
df = pd.read_csv('Datasets/Emotion/test_converted.csv')
texts = df['text'].tolist()
labels = df['mood'].tolist()
classes = sorted(list(set(labels)))

# ---------------- TF-IDF Features ----------------
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X = vectorizer.fit_transform(texts)
y = labels

# ---------------- Train Classifier ----------------
clf = LogisticRegression(max_iter=1000)
start_time = time.time()
clf.fit(X, y)
end_time = time.time()
training_time = end_time - start_time

# ---------------- Predictions ----------------
start_time = time.time()
y_pred = clf.predict(X)
end_time = time.time()
inference_time = end_time - start_time

# ---------------- Metrics ----------------
accuracy = accuracy_score(y, y_pred)
precision = precision_score(y, y_pred, average='weighted', zero_division=0)
recall = recall_score(y, y_pred, average='weighted', zero_division=0)
f1 = f1_score(y, y_pred, average='weighted', zero_division=0)

report = classification_report(y, y_pred, output_dict=True, zero_division=0)
report_df = pd.DataFrame(report).transpose()

cm = confusion_matrix(y, y_pred, labels=classes)

# ---------------- GUI Setup ----------------
root = tk.Tk()
root.title("Model Evaluation Dashboard")
root.geometry("1200x900")
root.configure(bg='white')

# Frame for Metrics
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

# 1. Confusion Matrix
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes, ax=axes[0,0])
axes[0,0].set_title('Confusion Matrix')
axes[0,0].set_xlabel('Predicted')
axes[0,0].set_ylabel('Actual')

# 2. Overall Metrics Bar Chart
metrics_df = pd.DataFrame({
    'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
    'Score': [accuracy, precision, recall, f1]
})
sns.barplot(x='Metric', y='Score', data=metrics_df, palette='viridis', ax=axes[0,1])
axes[0,1].set_ylim(0,1)
axes[0,1].set_title('Overall Model Metrics')

# 3. Class-wise Precision, Recall, F1
class_metrics = report_df.loc[classes, ['precision','recall','f1-score']].reset_index().melt(id_vars='index')
sns.barplot(x='index', y='value', hue='variable', data=class_metrics, palette='Set2', ax=axes[1,0])
axes[1,0].set_ylim(0,1)
axes[1,0].set_xlabel('Class')
axes[1,0].set_ylabel('Score')
axes[1,0].set_title('Class-wise Metrics')
axes[1,0].legend(title='Metric')

# 4. Class Distribution
sns.countplot(x=labels, palette='pastel', ax=axes[1,1])
axes[1,1].set_title('Actual Class Distribution')

# Embed Matplotlib Figure in Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(pady=10)

root.mainloop()
import torch
from torchvision import models, transforms
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import numpy as np

# Load checkpoint
checkpoint = torch.load('tuf_model_v1.pth', map_location='cpu', weights_only=False)
val_acc = checkpoint.get('val_acc', 0)
classes = checkpoint['classes']
print(f"Loaded val_acc from checkpoint: {val_acc:.2f}%")
print(f"Classes: {classes}")

# Prepare model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
base_model = models.mobilenet_v2(weights=None)
num_features = base_model.classifier[1].in_features
import torch.nn as nn
base_model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(num_features, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, len(classes))
)
base_model.load_state_dict(checkpoint['model_state_dict'])
base_model.to(device)
base_model.eval()

# Transform
IMAGE_SIZE = 224
val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Evaluate
base_dir = Path("dataset_hazirlik")
all_preds = []
all_labels = []

if base_dir.exists():
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
    for class_dir in base_dir.iterdir():
        if class_dir.is_dir() and class_dir.name in class_to_idx:
            label = class_to_idx[class_dir.name]
            for img_file in class_dir.iterdir():
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    try:
                        img = Image.open(img_file).convert('RGB')
                        img_tensor = val_transform(img).unsqueeze(0).to(device)
                        with torch.no_grad():
                            outputs = base_model(img_tensor)
                            _, pred = outputs.max(1)
                            all_preds.append(pred.item())
                            all_labels.append(label)
                    except Exception as e:
                        print(f"Error reading {img_file}: {e}")

# Calculate current accuracy on full dataset
if all_labels:
    correct = sum(1 for p, l in zip(all_preds, all_labels) if p == l)
    acc = correct / len(all_labels) * 100
    print(f"Evaluated on {len(all_labels)} images.")
    print(f"Current Accuracy (on full dataset): {acc:.2f}%")

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Confusion Matrix (Acc: {acc:.2f}%)')
    plt.tight_layout()
    plt.savefig('confusion_matrix_current.png')
    print("Saved confusion_matrix_current.png")

    # Bar chart of class distribution
    class_counts = [all_labels.count(i) for i in range(len(classes))]
    plt.figure(figsize=(10, 6))
    sns.barplot(x=classes, y=class_counts, palette='viridis')
    plt.title('Dataset Class Distribution')
    plt.ylabel('Number of Images')
    plt.xlabel('Classes')
    plt.tight_layout()
    plt.savefig('dataset_distribution_current.png')
    print("Saved dataset_distribution_current.png")
else:
    print("No images found for evaluation.")

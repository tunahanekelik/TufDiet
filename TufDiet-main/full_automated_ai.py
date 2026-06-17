import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

print("=" * 60)
print("Full Automated AI - Dataset Collection & Training")
print("=" * 60)

# ============================================================
# SECTION 1: LIBRARY CHECK AND INSTALLATION
# ============================================================
print("\n[1/6] Checking libraries...")

required_packages = {
    'torch': 'torch',
    'torchvision': 'torchvision',
    'numpy': 'numpy',
    'PIL': 'Pillow',
    'tqdm': 'tqdm',
    'requests': 'requests',
    'bs4': 'beautifulsoup4',
}

missing_packages = []

for pkg, install_name in required_packages.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg} already installed")
    except ImportError:
        missing_packages.append(install_name)
        print(f"  ✗ {pkg} not found - will be installed")

if missing_packages:
    print(f"\n  Installing: {', '.join(missing_packages)}")
    for pkg in missing_packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
    print("  ✓ All libraries installed")

print("\n[2/6] Creating folders...")

# ============================================================
# SECTION 2: FOLDER CREATION
# ============================================================
base_dir = Path("dataset_hazirlik")
categories = ["baklava", "salad", "chicken", "soup", "apple"]

for cat in categories:
    cat_dir = base_dir / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {cat_dir} created")

# ============================================================
# SECTION 3: AUTOMATIC IMAGE DOWNLOAD (Custom)
# ============================================================
print("\n[3/6] Downloading images...")

try:
    import requests
    from urllib.parse import urlparse
except ImportError:
    print("  Loading requests...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', '-q'])
    import requests
    from urllib.parse import urlparse

# Custom image download function (Unsplash API - more reliable)
def download_images_unsplash(query, output_dir, limit=50):
    """Download images from Unsplash"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    downloaded = 0
    
    # Try different sources
    sources = [
        # Unsplash search
        f"https://source.unsplash.com/random/224x224/?{query},food",
        # Getty Images like
        f"https://www.gettyimages.com/search?phrase={query}",
    ]
    
    # Simple web scraping - most popular free image sites
    search_queries = [
        f"{query} food photo",
        f"{query} delicious food",
    ]
    
    for sq in search_queries:
        if downloaded >= limit:
            break
            
        url = f"https://www.google.com/search?q={sq.replace(' ', '+')}&tbm=isch&hl=en"
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                continue
                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find images in JSON data
            import re
            img_data = re.findall(r'"https?://[^"]+\.(?:jpg|png|webp)"', response.text)
            
            for img_url in img_data[:limit]:
                if downloaded >= limit:
                    break
                img_url = img_url.strip('"')
                if not img_url.startswith('http'):
                    continue
                if 'base64' in img_url:
                    continue
                    
                try:
                    ext = '.jpg'
                    if '.png' in img_url.lower():
                        ext = '.png'
                    elif '.webp' in img_url.lower():
                        ext = '.webp'
                    
                    filename = output_dir / f"{query}_{downloaded:03d}{ext}"
                    img_resp = requests.get(img_url, headers=headers, timeout=10, stream=True)
                    if img_resp.status_code == 200:
                        content = img_resp.content
                        if len(content) > 5000:  # Minimum size check
                            with open(filename, 'wb') as f:
                                f.write(content)
                            downloaded += 1
                            print(f"    ✓ {downloaded}/{limit}")
                            time.sleep(0.5)
                except:
                    continue
        except Exception as e:
            continue
    
    # Alternative: Sample images (definitely working)
    if downloaded < 5:
        print(f"  ⚠ Trying alternative method...")
        sample_urls = [
            f"https://placehold.co/224x224/FF9900/white?text={query}",
        ]
        for i, url in enumerate(sample_urls):
            if downloaded >= limit:
                break
            try:
                filename = output_dir / f"{query}_sample{i}{'.png'}"
                img_resp = requests.get(url, timeout=10)
                if img_resp.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(img_resp.content)
                    downloaded += 1
            except:
                continue
    
    return downloaded

image_count = 50

for category in categories:
    print(f"\n  → {category} ({image_count} images) downloading...")
    try:
        downloaded = download_images_unsplash(category, base_dir / category, image_count)
        print(f"  ✓ {category}: {downloaded} images downloaded")
    except Exception as e:
        print(f"  ⚠ {category} error: {e}")
        continue

# ============================================================
# SECTION 4: MODEL TRAINING (PyTorch MobileNetV2)
# ============================================================
print("\n[4/6] Model training starting...")

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
from tqdm import tqdm

# Configuration
IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 15
LEARNING_RATE = 0.001
NUM_WORKERS = 0

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"  → Device: {device}")

# Custom Dataset class (with error handling)
class CustomFoodDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.classes = sorted([d.name for d in self.root_dir.iterdir() if d.is_dir()])
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.samples = self._load_samples()
        
    def _load_samples(self):
        samples = []
        for class_dir in self.root_dir.iterdir():
            if class_dir.is_dir():
                class_idx = self.class_to_idx[class_dir.name]
                for img_file in class_dir.iterdir():
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                        samples.append((str(img_file), class_idx))
        print(f"  → Loaded: {len(samples)} images, {len(self.classes)} classes")
        return samples
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label
        except Exception as e:
            print(f"  ⚠ Skipped image: {img_path} - {e}")
            # Return black image instead of corrupted image
            dummy = torch.zeros(3, IMAGE_SIZE, IMAGE_SIZE)
            return dummy, label

# Transformations (Data Augmentation)
train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE + 32, IMAGE_SIZE + 32)),
    transforms.RandomCrop(IMAGE_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Data loading
print("  ✓ Loading data...")
dataset = CustomFoodDataset(str(base_dir), transform=None)

train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

train_dataset.transform = train_transform
val_dataset.transform = val_transform

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

classes = dataset.classes
num_classes = len(classes)
print(f"  ✓ Classes: {classes}")
print(f"  ✓ Training: {len(train_dataset)}, Validation: {len(val_dataset)}")

# MobileNetV2 Model
print("  ✓ Loading MobileNetV2...")
base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
base_model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(base_model.classifier[1].in_features, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, num_classes)
)

# Backbone dondur
for param in base_model.features.parameters():
    param.requires_grad = False

model = base_model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

print("  ✓ Model compiled")

# Training loop
print(f"\n  ▶ Starting training ({EPOCHS} epochs)...")

best_val_acc = 0.0

for epoch in range(1, EPOCHS + 1):
    # Training
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    pbar = tqdm(train_loader, desc=f'Training {epoch}/{EPOCHS}')
    for batch_idx, (images, labels) in enumerate(pbar):
        if images is None:
            continue
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        _, predicted = outputs.max(1)
        train_total += labels.size(0)
        train_correct += predicted.eq(labels).sum().item()
        
        pbar.set_postfix({'acc': f'{100*train_correct/train_total:.1f}%'})
    
    train_acc = 100. * train_correct / train_total
    
    # Validation
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            if images is None:
                continue
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            _, predicted = outputs.max(1)
            val_total += labels.size(0)
            val_correct += predicted.eq(labels).sum().item()
    
    val_acc = 100. * val_correct / val_total
    scheduler.step()
    
    print(f"  Epoch {epoch}: Train Acc: {train_acc:.2f}%, Val Acc: {val_acc:.2f}%")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'classes': classes,
            'val_acc': val_acc,
        }, 'tuf_model_v1.pth')
        print(f"    ✓ Best model saved (Val Acc: {best_val_acc:.2f}%)")

# ============================================================
# SECTION 5: MODEL SAVING
# ============================================================
print("\n[5/6] Saving model...")

torch.save({
    'epoch': EPOCHS,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'classes': classes,
    'val_acc': best_val_acc,
}, 'tuf_model_v1.pth')

# Save class names
with open('food_classes.txt', 'w') as f:
    f.write('\n'.join(classes))

print("  ✓ tuf_model_v1.pth saved")
print("  ✓ food_classes.txt saved")

# ============================================================
# SECTION 6: SUMMARY
# ============================================================
print("\n[6/6] Training Summary:")
print(f"  - Best Validation Accuracy: {best_val_acc:.2f}%")
print(f"  - Number of Classes: {num_classes}")
print(f"  - Classes: {classes}")

print("\n" + "=" * 60)
print("COMPLETED! Model: tuf_model_v1.pth")
print("=" * 60)

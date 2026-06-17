import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from tqdm import tqdm

print("=" * 60)
print("Robust AI Training - TufDiet")
print("=" * 60)

# ============================================================
# SECTION 1: LIBRARY CHECK
# ============================================================
print("\n[1/5] Checking libraries...")

required_packages = {
    'torch': 'torch',
    'torchvision': 'torchvision',
    'numpy': 'numpy',
    'PIL': 'Pillow',
    'tqdm': 'tqdm',
}

for pkg, install_name in required_packages.items():
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', install_name, '-q'])

print("\n[2/5] Preparing dataset...")

# ============================================================
# SECTION 2: DATASET PREPARATION & CORRUPTED FILE CLEANUP
# ============================================================
class RobustDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.classes = sorted([d.name for d in self.root_dir.iterdir() if d.is_dir()])
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.samples = self._load_and_validate_samples()
        
    def _is_valid_image(self, img_path):
        """Check if the image is valid"""
        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                img.load()
            return True
        except Exception:
            return False
    
    def _load_and_validate_samples(self):
        """Load all samples and filter out corrupted ones"""
        samples = []
        invalid_count = 0
        
        for class_dir in self.root_dir.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                class_idx = self.class_to_idx[class_name]
                
                for img_file in class_dir.iterdir():
                    if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                        continue
                    
                    if self._is_valid_image(img_file):
                        samples.append((str(img_file), class_idx))
                    else:
                        invalid_count += 1
                        print(f"  ⚠ Corrupted: {img_file.name}")
        
        if invalid_count > 0:
            print(f"  → {invalid_count} corrupted images skipped")
        print(f"  ✓ Valid: {len(samples)} images, {len(self.classes)} classes")
        return samples
    
    def _load_samples(self):
        """Simple loading (with error handling)"""
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
            print(f"  ⚠ Atlanan: {Path(img_path).name}")
            return torch.zeros(3, IMAGE_SIZE, IMAGE_SIZE), label


# Configuration
IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 15
LEARNING_RATE = 0.001
NUM_WORKERS = 0

base_dir = Path("dataset_hazirlik")
if not base_dir.exists():
    print(f"  Error: {base_dir} folder not found!")
    sys.exit(1)

# Transforms
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

# Create Dataset
print("  ✓ Loading dataset...")
dataset = RobustDataset(str(base_dir), transform=None)

if len(dataset) == 0:
    print("  Error: No valid images found!")
    sys.exit(1)

train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

train_dataset.transform = train_transform
val_dataset.transform = val_transform

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, drop_last=False)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, drop_last=False)

classes = dataset.classes
num_classes = len(classes)
print(f"  ✓ Classes: {classes}")
print(f"  ✓ Training: {len(train_dataset)}, Validation: {len(val_dataset)}")

# ============================================================
# SECTION 3: MODEL CREATION
# ============================================================
print("\n[3/5] Creating model...")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"  → Device: {device}")

base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

base_model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(base_model.classifier[1].in_features, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, num_classes)
)

for param in base_model.features.parameters():
    param.requires_grad = False

model = base_model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)

print("  ✓ Model ready")

# ============================================================
# SECTION 4: TRAINING LOOP
# ============================================================
print(f"\n[4/5] Starting training ({EPOCHS} epochs)...")

best_val_acc = 0.0

for epoch in range(1, EPOCHS + 1):
    # Training
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    pbar = tqdm(train_loader, desc=f'Training {epoch}/{EPOCHS}')
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
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
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            _, predicted = outputs.max(1)
            val_total += labels.size(0)
            val_correct += predicted.eq(labels).sum().item()
    
    if val_total > 0:
        val_acc = 100. * val_correct / val_total
    else:
        val_acc = 0
    
    scheduler.step()
    
    print(f"  Epoch {epoch}: Train: {train_acc:.1f}%, Val: {val_acc:.1f}%")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'classes': classes,
            'val_acc': val_acc,
        }, 'tuf_model_v1.pth')
        print(f"    ✓ Best model saved")

# ============================================================
# SECTION 5: SAVING
# ============================================================
print("\n[5/5] Saving model...")

torch.save({
    'epoch': EPOCHS,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'classes': classes,
    'val_acc': best_val_acc,
}, 'tuf_model_v1.pth')

with open('food_classes.txt', 'w') as f:
    f.write('\n'.join(classes))

print("  ✓ tuf_model_v1.pth saved")
print("  ✓ food_classes.txt saved")

print("\n" + "=" * 60)
print(f"COMPLETED! Best accuracy: {best_val_acc:.2f}%")
print("=" * 60)

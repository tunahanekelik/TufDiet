import os
import sys
import subprocess
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from tqdm import tqdm

print("=" * 60)
print("Robust AI Training - TufDiet (FINAL)")
print("=" * 60)

# ============================================================
# LIBRARY CHECK
# ============================================================
print("\n[1/5] Checking libraries...")

for pkg, name in {'torch': 'torch', 'torchvision': 'torchvision', 'PIL': 'Pillow', 'tqdm': 'tqdm'}.items():
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', name, '-q'])

# ============================================================
# CONFIGURATION
# ============================================================
IMAGE_SIZE = 224
BATCH_SIZE = 8  # Reduced for small dataset
EPOCHS = 15
LEARNING_RATE = 0.001
NUM_WORKERS = 0

# Transforms - ALWAYS RETURN TENSOR
train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE + 32, IMAGE_SIZE + 32)),
    transforms.RandomCrop(IMAGE_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),  # ALWAYS TENSOR
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),  # ALWAYS TENSOR
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ============================================================
# DATASET - TENSOR GUARANTEED
# ============================================================
class TensorDataset(Dataset):
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
        return samples
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        # 1. Open the image
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            # If corrupted, return black tensor
            return torch.zeros(3, IMAGE_SIZE, IMAGE_SIZE), label
        
        # 2. Apply transform
        if self.transform:
            image = self.transform(image)
        
        # 3. GUARANTEE CHECK - Force convert if not tensor
        if not isinstance(image, torch.Tensor):
            image = transforms.ToTensor()(image)
        
        # 4. Final check
        assert isinstance(image, torch.Tensor), f"ERROR: Still PIL Image! {type(image)}"
        
        return image, label


def collate_fn(batch):
    """Filter None/corrupted data in batch"""
    # Filter out None values
    batch = [b for b in batch if b is not None and b[0] is not None]
    if not batch:
        return torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE), torch.zeros(1, dtype=torch.long)
    return torch.utils.data.dataloader.default_collate(batch)


# ============================================================
# DATA LOADING
# ============================================================
print("\n[2/5] Preparing dataset...")

base_dir = Path("dataset_hazirlik")
if not base_dir.exists():
    print(f"Error: {base_dir} not found!")
    sys.exit(1)

dataset = TensorDataset(str(base_dir), transform=None)
print(f"  → {len(dataset)} images, {len(dataset.classes)} classes: {dataset.classes}")

# Split
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])

# Transform atama
train_ds.dataset.transform = train_transform
val_ds.dataset.transform = val_transform

# DataLoader - collate_fn ile
train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, 
                          num_workers=NUM_WORKERS, collate_fn=collate_fn)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, 
                        num_workers=NUM_WORKERS, collate_fn=collate_fn)

print(f"  ✓ Training: {len(train_ds)}, Validation: {len(val_ds)}")

# ============================================================
# MODEL
# ============================================================
print("\n[3/5] Creating model...")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"  → Device: {device}")

base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
num_features = base_model.classifier[1].in_features

base_model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(num_features, 128),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(128, len(dataset.classes))
)

# Freeze backbone
for param in base_model.features.parameters():
    param.requires_grad = False

model = base_model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)

print("  ✓ Model ready")

# ============================================================
# TRAINING
# ============================================================
print(f"\n[4/5] Training starting ({EPOCHS} epochs)...")

best_val_acc = 0.0

for epoch in range(1, EPOCHS + 1):
    # Train
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    pbar = tqdm(train_loader, desc=f'Training {epoch}/{EPOCHS}')
    for images, labels in pbar:
        # Final safety check
        if not isinstance(images, torch.Tensor):
            print("  ⚠ Warning: images still not Tensor, skipping")
            continue
            
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
    
    train_acc = 100. * train_correct / max(train_total, 1)
    
    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            if not isinstance(images, torch.Tensor):
                continue
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            val_total += labels.size(0)
            val_correct += predicted.eq(labels).sum().item()
    
    val_acc = 100. * val_correct / max(val_total, 1)
    scheduler.step()
    
    print(f"  Epoch {epoch}: Train {train_acc:.1f}%, Val {val_acc:.1f}%")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'classes': dataset.classes,
            'val_acc': val_acc,
        }, 'tuf_model_v1.pth')
        print(f"    ✓ Saved")

# ============================================================
# SAVE
# ============================================================
print("\n[5/5] Saving...")

torch.save({
    'epoch': EPOCHS,
    'model_state_dict': model.state_dict(),
    'classes': dataset.classes,
    'val_acc': best_val_acc,
}, 'tuf_model_v1.pth')

with open('food_classes.txt', 'w') as f:
    f.write('\n'.join(dataset.classes))

print(f"\nCOMPLETED! Best: {best_val_acc:.1f}%")

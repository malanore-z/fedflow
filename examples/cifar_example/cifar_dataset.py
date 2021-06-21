import os

from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import transforms

from cifar_conf import CIFAR_ROOT


img_transforms = transforms.Compose(
    [
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ]
)


class CifarDataset(Dataset):

    def __init__(self, data):
        super(CifarDataset, self).__init__()
        self.imgs = []
        self.labels = []
        self.read_imgs(data)

    def __getitem__(self, item):
        return img_transforms(self.imgs[item]), self.labels[item]

    def __len__(self):
        return len(self.imgs)

    def read_imgs(self, data):
        for d in data:
            path = os.path.join(CIFAR_ROOT, d[0])
            img = Image.open(path)
            self.imgs.append(img.copy())
            self.labels.append(d[1])
            img.close()

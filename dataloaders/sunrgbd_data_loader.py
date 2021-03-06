
from __future__ import print_function, division
import os
import sys
from tqdm import *
import pandas as pd
import numpy as np
from numpy import random
from PIL import Image
import skimage
import PIL
import matplotlib.pyplot as plt
from skimage import io, transform
from skimage.color import rgb2lab
from skimage.util import random_noise
#import image_slicer

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
from torch.autograd import Variable
import torchvision.transforms.functional as TF

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

plt.ion()   # interactive mode

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])

class SUN_RGBD_dataset_train():
    """ SUN-RGBD dataset - RGB-D semantic labeling.
    Download datset from : http://cvgl.stanford.edu/data2/sun_rgbd.tgz
    """

    def __init__(self,img_dir,depth_dir,mask_dir,seed_dir=None,transform=None,sizes=[(280,360),(240,320)]):
        """
        Args:
            mask_dir (string): Path to (img) annotations.
            img_dir (string): Path with all the training images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.img_dir = img_dir
        self.depth_dir = depth_dir
        self.mask_dir = mask_dir
        self.transform = transform
        self.img_names = os.listdir(img_dir)
        self.depth_names = os.listdir(depth_dir)
        self.label_names = os.listdir(mask_dir)
 
        self.sizes = sizes
        
        self.img_names.sort()
        self.depth_names.sort()
        self.label_names.sort()


    def __len__(self):
        return len(self.img_names)
    
    def _transform(self, image, depth, mask,sizes=[(280,360),(240,320)]):
        # Resize
        resize = transforms.Resize(size=sizes[0])
        image = resize(image)
        depth = resize(depth)
        mask = resize(mask)

        normalize1 = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
        normalize2 = transforms.Normalize(mean=[19050],std=[9650])


        # Random crop
        i, j, h, w = transforms.RandomCrop.get_params(
            image, output_size=sizes[1])
        image = TF.crop(image, i, j, h, w)
        depth = TF.crop(depth, i, j, h, w)
        mask = TF.crop(mask, i, j, h, w)
 
        # Random horizontal flipping
        if random.random() > 0.5:
            image = TF.hflip(image)
            depth = TF.hflip(depth)
            mask = TF.hflip(mask)

        orimage = image
        
        # Transform to tensor
        image = TF.to_tensor(image).type('torch.FloatTensor')
        depth = TF.to_tensor(depth).type('torch.FloatTensor')
        #mask = TF.to_tensor(mask).type('torch.FloatTensor')
        mask = torch.from_numpy(np.array(mask)).type('torch.FloatTensor')

        #orimage = pyCMS.profileToProfile(image, pyCMS.createProfile("sRGB"), pyCMS.createProfile("LAB"))
        #orimage = rgb2lab(random_noise(orimage,mode='gaussian',var=0.0002))
        orimage = rgb2lab(orimage)
        orimage = torch.from_numpy(np.array(orimage)).type('torch.FloatTensor')
        #print (mask)
        #sys.exit(0)

        # normalize
        image = normalize1(image)
        depth = normalize2(depth)
        return image, depth, mask, orimage
    def __getitem__(self, idx):
        #print ('\tcalling Dataset:__getitem__ @ idx=%d'%idx)
        image = Image.open(os.path.join(self.img_dir,self.img_names[idx])).convert('RGB')
        depth = Image.open(os.path.join(self.depth_dir,self.depth_names[idx]))
        label = Image.open(os.path.join(self.mask_dir,self.label_names[idx]))
        
        #ori_image = io.imread(os.path.join(self.img_dir,self.img_names[idx]))
        #if self.transform:
        #    image = self.transform(image).type('torch.FloatTensor')
        #    depth = self.transform(depth).type('torch.FloatTensor')
        #    label = self.transform(label).type('torch.FloatTensor')
        image, depth, label, orimage = self._transform(image,depth,label,sizes=self.sizes)
        return image, depth, label, orimage



class SUN_RGBD_dataset_val():
    """SUN-RGBD image semantic labeling dataset."""

    def __init__(self,img_dir,depth_dir,mask_dir,transform=None,sizes=[(240,320),(240,320)]):
        """
        Args:
            mask_dir (string): Path to (img) annotations.
            img_dir (string): Path with all the training images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.mask_dir = mask_dir
        self.depth_dir = depth_dir
        self.img_dir = img_dir
        self.transform = transform
        self.img_names = os.listdir(img_dir)
        self.depth_names = os.listdir(depth_dir)
        self.label_names = os.listdir(mask_dir)
        self.size = sizes[1]

        self.img_names.sort()
        self.depth_names.sort()
        self.label_names.sort()


    def __len__(self):
        return len(self.img_names)

    def __getitem__(self, idx):
        """
        return:
            image,depth,label,image path (for visualization)
        """
        #print ('\tcalling Dataset:__getitem__ @ idx=%d'%idx)
        image = Image.open(os.path.join(self.img_dir,self.img_names[idx])).convert('RGB')
        depth = Image.open(os.path.join(self.depth_dir,self.depth_names[idx]))
        label = np.array(Image.open(os.path.join(self.mask_dir,self.label_names[idx])))
       
        if self.transform:
            normalize1 = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
            normalize2 = transforms.Normalize(mean=[19050],std=[9650])

            image = self.transform(image).type('torch.FloatTensor')
            depth = self.transform(depth).type('torch.FloatTensor')
            #print (label)
            #label = self.transform(label).type('torch.FloatTensor')
            label = skimage.transform.resize(label, self.size, order=0,
                    mode='reflect', preserve_range=True)
            label = torch.from_numpy(label).type('torch.FloatTensor')
            #print (label)
            image = normalize1(image)
            depth = normalize2(depth)
            # normalize
        #print(label.size())
        #return image, label, name, (original_image.size[0],original_image.size[1])


        return image, depth, label, os.path.join(self.img_dir,self.img_names[idx])


class sunrgbd_drawer():
    def __init__(self):
        self.n_classes = None
    def decode_segmap(self, label_mask, n_classes, plot=False):
        """Decode segmentation class labels into a color image
        Args:
            label_mask (np.ndarray): an (M,N) array of integer values denoting
              the class label at each spatial location.
            plot (bool, optional): whether to show the resulting color image
              in a figure.
        Returns:
            (np.ndarray, optional): the resulting decoded color image.
        """
        #label_colours = self.get_pascal_labels()
        label_colours = None
        if n_classes == 14:
            label_colours = self.get_14_colors()
        else:
            label_colours = self.get_spaced_colors(n_classes)
        r = label_mask.copy()
        g = label_mask.copy()
        b = label_mask.copy()
        #print (label_colours.shape)
        #print (label_colours[0,0])
        #sys.exit(0)
        for ll in range(n_classes):
            r[label_mask == ll] = label_colours[ll, 0]
            g[label_mask == ll] = label_colours[ll, 1]
            b[label_mask == ll] = label_colours[ll, 2]
        #print (r.shape) # (640,480)
        #print (r[1])
        rgb = np.zeros((label_mask.shape[0], label_mask.shape[1], 3))
        #print (rgb[:,:,0].shape,r.shape)
        #rgb[:, :, 0] = r / 255.0
        rgb[:, :, 0] = r 
        #rgb[:, :, 1] = g / 255.0
        rgb[:, :, 1] = g 
        #rgb[:, :, 2] = b / 255.0
        rgb[:, :, 2] = b 
        if plot:
            plt.imshow(rgb)
            plt.show()
        else:
            return rgb
    
    def get_14_colors(self):
        """Load the mapping that associates pascal classes with label colors
            Returns:
                np.ndarray with dimensions (13, 3)
        """
        return np.asarray(
            [
                [0, 0, 0],
                [128, 0, 0],
                [0, 128, 0],
                [128, 128, 0],
                [0, 0, 128],
                [128, 0, 128],
                [0, 128, 128],
                [128, 128, 128],
                [64, 0, 0],
                [192, 0, 0],
                [64, 128, 0],
                [192, 128, 0],
                [64, 0, 128],
                [192, 0, 128],
                #[64, 128, 128],
                #[192, 128, 128],
                #[0, 64, 0],
                #[128, 64, 0],
                #[0, 192, 0],
                #[128, 192, 0],
                #[0, 64, 128],
                # 21 above 
                ]
            ) 
    def get_spaced_colors(self,n):
        max_value = 16581375 #255**3
        interval = int(max_value / n)
        colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
        
        return np.array([[int(i[:2], 16), int(i[2:4], 16), int(i[4:], 16)] for i in colors]  )

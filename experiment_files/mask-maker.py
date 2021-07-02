
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

my_dpi = 96 # dpi of the lab monitor
desired_pixels = 684
desired_figsize = desired_pixels/my_dpi

# defining the variables
sigma = 37.5
muu = 180
radius = 240
smoothness = 100  # smoothness of the blur

theta = np.linspace(-2*np.pi, 2*np.pi, desired_pixels)

x = radius * np.cos(theta)
y = radius * np.sin(theta)

x, y = np.meshgrid(x, y)

# calculating the distance of all points to the center
distance = np.sqrt(x*x + y*y)

# calculating the Gaussian array
gauss = (1 / sigma * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ( ( distance - muu ) / sigma)**2)

# plotting the mask
plt.gray()
plt.figure(figsize=(desired_figsize, desired_figsize), dpi=my_dpi, tight_layout=True, frameon=False)
ax = plt.gca()
ax.set_aspect(1)
ax.contourf(x, y, gauss, smoothness)
ax.axis('off')

plt.savefig("mask.png", dpi=my_dpi)

# import the mask and convert it to a numpy array
img = Image.open('mask.png').convert('LA')

maskarray = np.asarray(img)
maskarray = maskarray[:,:,0]

maskarray = np.interp(maskarray, (maskarray.min(), maskarray.max()), (-1, +1)) # normalize [-1,1]
maskarray[np.where(maskarray == 1)] = -1

np.save('maskarray', maskarray)
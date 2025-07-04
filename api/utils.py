import os
from django.conf import settings
import matplotlib.pyplot as plt

def save_plot(filename):
    media_root = getattr(settings, 'MEDIA_ROOT', 'media')
    if not os.path.exists(media_root):
        os.makedirs(media_root)
    filepath = os.path.join(media_root, filename)
    plt.savefig(filepath)
    plt.close()
    return f'/media/{filename}' 
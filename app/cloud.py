import os
import numpy as np
from PIL import Image
from scipy.misc import imread

import matplotlib.pyplot as plt

from palettable.colorbrewer.sequential import Reds_9
from palettable.colorbrewer.sequential import Greens_9

from wordcloud import WordCloud, STOPWORDS


def green_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Greens_9.colors[np.random.randint(5,9)])

def red_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Reds_9.colors[np.random.randint(5,9)])

def cloud_to_fig(cloud):
    fig,ax = plt.subplots()
    fig.tight_layout()
    ax.imshow(cloud)
    ax.axis('off')
    return fig

def save_member_cloud(fig,member,key):
    path = '/static/word_clouds/'+\
           key+'_'+member.first_name+'_'+\
           member.last_name+'.png'
    fig.savefig('app/'+path, bbox_inches='tight')
    return path

def make_word_cloud(word_freq, type='Yea'):
    """Make a word cloud from a list of words"""
    if type =='Yea':
        thumb = Image.open('app/static/img/thumbs-up.png')
        color_func = green_color_func
    elif type == 'Nay':
        thumb = Image.open('app/static/img/thumbs-down.png')
        color_func = red_color_func
    else:
        thumb = Image.open('app/static/img/thumbs-up.png')
        color_func = green_color_func
        
    mask = Image.new("RGB", thumb.size, (255,255,255))
    mask.paste(thumb,thumb)
    mask = np.array(mask)
    
    wc = WordCloud(background_color='white',
                   max_words=100,
                   mask=mask,
                   stopwords=STOPWORDS)
    #wc = wc.generate_from_frequencies(word_freq)
    wc = wc.generate(' '.join(word_freq.keys()))
    wc = wc.recolor(color_func=color_func)
    fig = cloud_to_fig(wc)
    return fig

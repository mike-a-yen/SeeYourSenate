from app import BASE_DIR
from app.member_topics import vote_topic_freq
from app.build_models import stopwords

import pdb

import os
import numpy as np
import glob
from PIL import Image
from scipy.misc import imread

import matplotlib
import mpld3
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from palettable.colorbrewer.sequential import Reds_9
from palettable.colorbrewer.sequential import Greens_9
from palettable.colorbrewer.sequential import Blues_9

from wordcloud import WordCloud, STOPWORDS


def green_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Greens_9.colors[np.random.randint(5,9)])

def red_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Reds_9.colors[np.random.randint(5,9)])

def blue_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Blues_9.colors[np.random.randint(5,9)])

def cloud_to_fig(cloud):
    fig,ax = plt.subplots(figsize=(7,7))
    fig.tight_layout()
    ax.imshow(cloud,origin='lower')
    #ax.xaxis.set_visible(False)
    #ax.yaxis.set_visible(False)
    ax.set_frame_on(False)
    ax.xaxis.set_major_formatter(plt.NullFormatter())
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    #ax.axis('off')
    return fig

def save_member_cloud(html,member,key):
    file_name = key+'_'+member.first_name+'_'+member.last_name+'.html'
    path = os.path.join(BASE_DIR,'app/static/word_clouds',
                        file_name)
    fo = open(path,'w')
    fo.write(html)
    return path

def make_word_cloud(member):
    base_path = os.path.join(BASE_DIR,'app','static','word_clouds')
    cloud_path = os.path.join(base_path,'*%s*%s.html'%(member.first_name,
                                                      member.last_name))
    if glob.glob(cloud_path):
        paths = {'Yea':BASE_DIR+'/app/static/word_clouds/Yea_%s_%s.html'%(member.first_name,
                                                                          member.last_name),
                 'Nay':BASE_DIR+'/app/static/word_clouds/Nay_%s_%s.html'%(member.first_name,
                                                                          member.last_name)}
        return {key:open(path,'r').read() for key,path in paths.items()}
    else: # make clouds
        topic_freqs = vote_topic_freq(member.member_id)
        clouds = {key:generate_word_cloud(word_freqs,key)\
                  for key,word_freqs in topic_freqs.items()}
        paths = {key:save_member_cloud(html,member,key)\
                 for key,html in clouds.items()}
    return clouds

def generate_word_cloud(word_freq, type='Yea'):
    """Make a word cloud from a list of words"""
    if type =='Yea':
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-up.png')
        color_func = green_color_func
    elif type == 'Nay':
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-down.png')
        color_func = red_color_func
    else:
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-up.png')
        color_func = green_color_func
    
    mask = Image.new("RGB", thumb.size, (255,255,255))
    mask.paste(thumb,thumb)
    mask = np.array(mask)
    
    wc = WordCloud(background_color='white',
                   width=4000,
                   height=4000,
                   max_words=225,
                   mask=mask,
                   stopwords=stopwords)
    wc = wc.generate_from_frequencies(word_freq)
    #wc = wc.generate(words)
    wc = wc.recolor(color_func=color_func)
    fig = cloud_to_fig(wc)
    return mpld3.fig_to_html(fig)

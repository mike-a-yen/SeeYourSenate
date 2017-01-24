from app import BASE_DIR
from app.member_topics import vote_topic_freq
from app.build_models import stopwords

import os
from functools import partial
import numpy as np
import glob
from PIL import Image
from scipy.misc import imread

import matplotlib
import mpld3
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from palettable.colorbrewer.sequential import Greens_9, Reds_9, Greys_9, Blues_9

from wordcloud import WordCloud


def word_cloud_color_table(cloud,color_map,scale=(4,8)):
    word_counts = {x[0]:x[1] for x in cloud.words_}
    n_buckets = scale[1]-scale[0]
    word_bucket = {word:int(count*n_buckets+scale[0]) for word,count in word_counts.items()}
    word_color_table = {word:color_map.colors[bucket] for word,bucket in word_bucket.items()}
    return word_color_table

def scalable_color(word, font_size, position, orientation,
                         random_state=None, word_color_table=None,**kwargs):
    return tuple(word_color_table[word])
    
def green_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    print(word,font_size)
    return tuple(Greens_9.colors[np.random.randint(5,9)])

def red_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Reds_9.colors[np.random.randint(5,9)])

def blue_color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
    return tuple(Blues_9.colors[np.random.randint(5,9)])

def cloud_to_fig(cloud):
    print('Cloud to Fig')
    fig,ax = plt.subplots(figsize=(7,7))
    fig.tight_layout()
    print('imshow')
    print(cloud)
    ax.imshow(cloud,origin='lower')
    #ax.set_frame_on(False)
    print('remove axis')
    ax.xaxis.set_major_formatter(plt.NullFormatter())
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    print('done in cloud to fig')
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
    counts = [x[1] for x in word_freq]
    if type =='Yea':
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-up.png')
        color_map = Greens_9
    elif type == 'Nay':
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-down.png')
        color_map = Reds_9
    else:
        thumb = Image.open(BASE_DIR+'/app/static/img/thumbs-up.png')
        color_map = Greys_9

    mask = Image.new("RGB", thumb.size, (255,255,255))
    mask.paste(thumb,thumb)
    mask = np.array(mask)
    
    wc = WordCloud(background_color='white',
                   width=4000,
                   height=4000,
                   max_words=200,
                   mask=mask,
                   stopwords=stopwords)
    wc = wc.generate_from_frequencies(word_freq)

    word_color_table = word_cloud_color_table(wc,color_map,scale=(4,8))
    print(word_color_table)
    color_func = partial(scalable_color,word_color_table=word_color_table)    
    #wc = wc.generate(words)
    wc = wc.recolor(color_func=color_func)
    fig = cloud_to_fig(wc)
    return mpld3.fig_to_html(fig)

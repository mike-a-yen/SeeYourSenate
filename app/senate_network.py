#from app import db, BASE_DIR
#from app.models import *
#from app.member_utils import vote_map
#from app.utils import get_senate

import networkx as nx
import community
import itertools as it
import numpy as np
import scipy
import scipy.linalg as LA
import scipy.sparse as sps

"""
Create a network for senators to find groups that have similar voting patterns
For each session, split the members by their vote
For each unique member pair who casts vote, increment their edge weight by 1

"""

def create_network(member_ids,sessions):
    G = nx.Graph()
    G.add_nodes_from(member_ids)

    pairs = it.combinations(member_ids,2)
    for pair in pairs:
        G.add_edge(*pair,similarity_count=0,
                   dissimilarity_count=0,
                   similarity_score=0,
                   total_count=0)
        
    for session in sessions:
        member_session = db.session.query(MemberSession)\
                            .filter_by(session_id=session.session_id).all()
        record = [(ms.member_id,ms.vote) for ms in member_session]
        pairs = it.combinations(record,2)
        for pair in pairs:
            vote1,vote2 = vote_map(pair[0][1]),vote_map(pair[1][1])
            mem1, mem2 = pair[0][0],pair[1][0]
            
            G.edge[mem1][mem2]['total_count'] += 1
            if vote1 == vote2:
                G.edge[mem1][mem2]['similarity_count'] += 1
            else:
                G.edge[mem1][mem2]['dissimilarity_count']+=1

    for n1,n2,attr in G.edges(data=True):
        if attr['total_count']!=0:
            attr['similarity_score'] = (attr['similarity_count']-attr['dissimilarity_count'])\
                                       /attr['total_count']
    return G


def laplacian_norm(affinity):
    degree = np.diag(affinity.sum(axis=1))
    degree_sqrt_inv = LA.inv(LA.sqrtm(degree))
    I = np.eye(len(affinity))
    L = I - np.dot(degree_sqrt_inv,
                   np.dot(affinity,degree_sqrt_inv))
    L[np.abs(L) < 1e-5] = 0
    return scipy.real(L)
    
def eigensystem(L):
    w,v = LA.eig(L)
    w_sorted = np.sort(scipy.real(w))
    v_sorted = v[np.argsort(scipy.real(w))]
    return w_sorted, v_sorted
    
if __name__=='__main__':
    #affinity = np.array([[0,10,1],[10,0,0],[1,0,0]])
    #L = laplacian_norm(affinity)
    #members = get_senate(114)
    #member_ids = [mem.member_id for mem in members]
    #sessions = db.session.query(Session).filter_by(congress_id=114).all()
    #G = create_network(member_ids,sessions)
    #nx.write_gpickle(G,'graph.gpickle')
    G = nx.read_gpickle('graph.gpickle')
    #graph = nx.to_numpy_recarray(G,dtype=[('similarity_score',float),
    #                                      ('similarity_count',int),
    #                                      ('dissimilarity_count',int),
    #                                      ('total_count',int)])
    #np.savetxt('similarity_score.np',graph['similarity_score'])
    similarity_score = np.genfromtxt('similarity_score.np')
    partition = community.best_partition(G,weight='similarity_score')
    #L = laplacian_norm(similarity_score)
    #L = sps.csgraph.laplacian(similarity_score)
    #w,v = eigensystem(L)
    #partition = community(G)

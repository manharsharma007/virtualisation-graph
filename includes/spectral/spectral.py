#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import networkx as nx

class Spectral(object):
    def __init__(self):
        self.G = None
        self.Pos = None
        self.eigenvalues = None
        self.eigenvectors = None
    
    def compute(self, G):
        self.G = G

        A=nx.to_numpy_matrix(G)
        nnodes,_=A.shape
        A=np.asarray(A)
        I=np.identity(nnodes,dtype=A.dtype)
        D=I*np.sum(A,axis=1) # diagonal of degrees
        L=D-A

        self.eigenvalues, self.eigenvectors=np.linalg.eig(L)
        # sort and keep smallest nonzero
        index=np.argsort(self.eigenvalues)[1:2+1] # 0 index is zero eigenvalue
        self.Pos = np.real(self.eigenvectors[:,index])
        self.Pos=self._rescale_layout(self.Pos,1)
        self.Pos = dict(zip(G,self.Pos))

        return self.Pos

    def _rescale_layout(self, pos,scale=1):
        # rescale to (0,pscale) in all axes

        # shift origin to (0,0)
        lim=0 # max coordinate for all axes
        for i in range(pos.shape[1]):
            pos[:,i]-=pos[:,i].min()
            lim=max(pos[:,i].max(),lim)
        # rescale to (0,scale) in all directions, preserves aspect
        for i in range(pos.shape[1]):
            pos[:,i]*=scale/lim
        return pos
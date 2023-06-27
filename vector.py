# Authors: Marcel Gunadi, Trien Bang Huynh and Minh Duc Vo

import numpy as np

class Vector:
    def __init__(self):
       pass

    def normalize_year(self,v):
        '''Normalize year of vector v to (-1, 1)'''
        if len(v[0]) == 3:
            v[:, 0] -= 1988.5
            v[:, 0] /= 33.5
        v[:, len(v[0]) - 2] -= 300
        v[:, len(v[0]) - 2] /= 300
        v[:, len(v[0]) - 1] /= 100
        return v

    def angle_between_vectors(self,v1, v2, locked = False):
        '''
        In:
        v1: One 3D vector (np array) (m,) (may be (Year, Revenue, Profit) or (Revenue, Profit))
        v2: Multiple 3D vectors (np array) (n, m,)
        locked: lock year?
        Out:
        Multiple angles between v1 and each vector in v2 (n,)
        '''
        if len(v1) < 3:
            if v1.ndim < 2:
                v1 = np.array([v1])
            vv1 = v1.copy()
            vv2 = v2[:,1:].copy()
            if locked:
                raise Exception("Please specify year when choose to lock the year (cannot be both 2d v1 vector and locked = True)")
        else:
            if v1.ndim < 2:
                v1 = np.array([v1])
            vv1 = v1.copy()
            vv2 = v2.copy()
        vv2 = vv2.T
        if locked:
            arr = np.dot(vv1, vv2)[0] / (np.linalg.norm(vv1, axis = 1) * np.linalg.norm(vv2, axis = 0))
            v3 = np.arccos(arr - 0.00001)
            v4 = vv2[0] != vv1[0][0]
            v3[v4] = 3.1415927
        else:
            arr = np.dot(vv1, vv2)[0] / (np.linalg.norm(vv1, axis = 1) * np.linalg.norm(vv2, axis = 0))
            v3 = np.arccos(arr - 0.00001)

        # print(vv1.shape, vv2.shape)
        return v3

    def distance_between_vectors(self,v1, v2, locked = False):
        '''
        In:
        v1: One 3D vector (np array) (m,)
        v2: Multiple 3D vectors (np array) (n, m,)
        locked: lock year?
        Out:
        Multiple angles between v1 and each vector in v2 (n,)
        '''
        vv1 = v1.copy()
        vv2 = v2.copy()
        if len(vv1) < 3:
            vv1 = self.normalize_year(np.array([vv1]))
            vv2 = self.normalize_year(vv2[:, 1:])
            if locked:
                raise Exception("Please specify year when choose to lock the year (cannot be both 2d v1 vector and locked = True)")
            print(vv1.shape, vv2.shape)
            return np.linalg.norm((vv2 - vv1), axis = 1)
        if locked:
            mul = sum(vv2[:,0]) * 1e3
            vv1[0] *= mul
            vv2[:, 0] *= mul
        vv1 = self.normalize_year(np.array([vv1]))
        vv2 = self.normalize_year(vv2)
        # print(vv1.shape, vv2.shape)
        return np.linalg.norm(vv2 - vv1, axis = 1)

"""
ignore this file
"""

import pandas as pd
import numpy as np

def a(p,k):
    top = 3**k*p
    bot = (3**(3-k)*p + 3**k*(1-p))
    return top / bot

def b(p,k):
    return p/(3**(3-k))

def c(p,k):
    top = p*3**(3-k)
    bot = 3**(3-k)*p+3**k*(1-p)
    return top/bot

def d(p,k):
    top = (1-p)*3**(3-k)
    bot = 3**(3-k)*p+3**k*(1-p)
    return top/bot

def mine(p,k):
    top = p*3**(3-k)/4**3
    bot = top + (1-p)*3**k/4**3
    return top/bot

import scipy.integrate

lmbda = 3
mu = 4
PA = 3/4
PB = 1/4

def f_T1T2_A(x,y):
    return lmbda*lmbda*np.exp(-lmbda*(x+y))

def f_T1T2_B(x,y):
    return mu*mu*np.exp(-mu*(x+y))

def f_T1T2(x,y):
    return PA*f_T1T2_A(x,y) + PB*f_T1T2_B(x,y)

def f_T2(x):
    return f_T1T2(2,x)

def f_T1(x):
    return scipy.integrate.quad(lambda y: f_T1T2(x,y), 0, 40)[0]

# expt = scipy.integrate.quad(lambda x: x*f_T2(x), 0, 40)[0]
# print(expt / f_T1(2))

print(4/15*4/5*1/4/(4/45*(8-(5/4)**3)))
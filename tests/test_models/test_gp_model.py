
import random
random.seed(12345)

import pytest
import numpy as np 
import warnings

from GPy.models import GPRegression

from GPdoemd.models import GPModel
from GPdoemd.kernels import RBF
from GPdoemd.marginal import TaylorFirstOrder

"""
SET UP MODEL ONCE
"""

x_bounds = np.array([[10., 20.], [5., 8.]])
p_bounds = np.array([[ 2.,  4.], [3., 5.]])
z_bounds = np.array( x_bounds.tolist() + p_bounds.tolist() )

def f (x, p):
	return x * p

#ymin = np.array([20,15])
#ymax = np.array([80,40])

d = {
	'name':        'testmodel',
	'call':        f,
	'dim_x':       len(x_bounds),
	'dim_p':       len(p_bounds),
	'num_outputs': 2
}
M = GPModel(d)


X  = np.array([[10., 5.], [10., 8.], [20., 5.], [20., 8.]])
Xs = np.random.uniform([10, 5], [20, 8], size=(10,2))
X = np.vstack(( X, Xs ))

P  = np.array([[2., 3.], [2., 5.], [4., 3.], [4., 5.]])
Ps = np.random.uniform([2., 3.], [4., 5.], size=(10,2))
P = np.vstack(( P, Ps ))

Z = np.c_[X, P]
Y = f(X, P)
M.set_training_data(Z, Y)

ymean = np.mean( Y, axis=0 )
ystd  = np.std(  Y, axis=0 )


"""
TESTS
"""

class TestGPModel:

	"""
	Dimensions
	"""
	def test_dim_x (self):
		assert M.dim_b == 0

	"""
	Forward transformations
	"""
	def test_trans_z_min (self):
		assert np.all( np.min(M.Z, axis=0) == np.zeros(4) )

	def test_trans_z_max (self):
		assert np.all( np.max(M.Z, axis=0) == np.ones(4)  )

	def test_trans_x_min (self):
		assert np.all( np.min(M.X, axis=0) == np.zeros(2) )

	def test_trans_x_max (self):
		assert np.all( np.max(M.X, axis=0) == np.ones(2)  )

	def test_trans_p_min (self):
		assert np.all( np.min(M.P, axis=0) == np.zeros(2) )

	def test_trans_p_max (self):
		assert np.all( np.max(M.P, axis=0) == np.ones(2)  )

	def test_trans_y_mean (self):
		assert np.all( np.abs(np.mean(M.Y, axis=0)) <= 1e-10 )

	def test_trans_y_std (self):
		assert np.all( np.abs(np.std(M.Y, axis=0) - 1) <= 1e-10 )

	"""
	Backward transformations
	"""
	def test_backtrans_z_min (self):
		t = M.backtransform_z( np.zeros(4) )
		assert np.all(t == z_bounds[:, 0])

	def test_backtrans_z_max (self):
		t = M.backtransform_z( np.ones(4)  )
		assert np.all(t == z_bounds[:, 1])

	def test_backtrans_x_min (self):
		t = M.backtransform_x( np.zeros(2) )
		assert np.all(t == x_bounds[:, 0])

	def test_backtrans_x_max (self):
		t = M.backtransform_x( np.ones(2)  )
		assert np.all(t == x_bounds[:, 1])
		
	def test_backtrans_p_min (self):
		t = M.backtransform_p( np.zeros(2) )
		assert np.all(t == p_bounds[:, 0])

	def test_backtrans_p_max (self):
		t = M.backtransform_p( np.ones(2)  )
		assert np.all(t == p_bounds[:, 1])
	
	def test_backtrans_y_mean (self):
		yt    = M.backtransform_y( np.zeros(2) )
		assert np.all(yt == ymean)

	def test_backtrans_y_std (self):
		yt   = np.std( M.backtransform_y( M.Y ), axis=0)
		assert np.all( np.abs(yt - ystd) <= 1e-10 )


	"""
	Transform variance vectors
	"""
	def _trans_var (self, C, m, M):
		return C / (M - m)**2

	def test_trans_p_var (self):
		C  = np.array([5., 2.])
		Ct = self._trans_var(C, p_bounds[:,0], p_bounds[:,1])
		Cp = M.transform_p_var( C )
		assert np.all( np.abs(Ct - Cp) <= 1e-10 )
		assert np.all( np.abs(C - M.backtransform_p_var(Cp)) <= 1e-10 )

	def test_trans_y_var (self):
		C  = np.array([5., 2.])
		Ct = self._trans_var(C, 0, ystd)
		Cp = M.transform_y_var( C )
		assert np.all( np.abs(Ct - Cp) <= 1e-10 )
		assert np.all( np.abs(C - M.backtransform_y_var(Cp)) <= 1e-10 )


	"""
	Transform covariances matrices
	"""
	def _trans_cov (self, C, m, M):
		mt = M - m
		return C / (mt[:,None] * mt[None,:])

	def test_trans_p_cov (self):
		C  = np.array([[5., 3.], [3., 2.]])
		Ct = self._trans_cov(C, p_bounds[:,0], p_bounds[:,1])
		Cp = M.transform_p_cov( C )
		assert np.all( np.abs(Ct - Cp) <= 1e-10 )
		assert np.all( np.abs(C - M.backtransform_p_cov(Cp)) <= 1e-10 )

	def test_trans_y_cov (self):
		C  = np.array([[5., 3.], [3., 2.]])
		Ct = self._trans_cov(C, 0, ystd)
		Cp = M.transform_y_cov( C )
		assert np.all( np.abs(Ct - Cp) <= 1e-10 )
		assert np.all( np.abs(C - M.backtransform_y_cov(Cp)) <= 1e-10 )


	"""
	Transform None
	"""
	def test_none_transform (self):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			# Forward transform
			assert np.isnan(M.transform( M.box_trans, M.X,  M.xmin,   None))
			assert np.isnan(M.transform( M.box_trans, M.X,    None, M.xmax))
			assert np.isnan(M.transform( M.box_trans, None, M.xmin, M.xmax))
			# Backward transform
			assert np.isnan(M.backtransform( M.box_trans, M.X,  M.xmin,   None))
			assert np.isnan(M.backtransform( M.box_trans, M.X,    None, M.xmax))
			assert np.isnan(M.backtransform( M.box_trans, None, M.xmin, M.xmax))

	"""
	Test training data
	"""
	def _is_none (self, M):
		for v in ['X', 'P', 'Z']:
			assert eval('M.'+v.upper()) is None
			assert eval('M.'+v.lower()+'min') is None
			assert eval('M.'+v.lower()+'max') is None
		assert M.Y is None
		assert M.ymean is None
		assert M.ystd  is None

	def _correct_shape (self, M):
		for v in ['X', 'P']:
			assert eval('M.'+v.upper()).shape       == X.shape
			assert eval('M.'+v.lower()+'min').shape == (2,)
			assert eval('M.'+v.lower()+'max').shape == (2,)
		assert M.Y.shape     == X.shape
		assert M.ymean.shape == (2,)
		assert M.ystd.shape  == (2,)
		assert M.Z.shape     == Z.shape
		assert M.zmin.shape  == (4,)
		assert M.zmax.shape  == (4,)

	def test_training_data (self):
		Mt = GPModel(d)
		self._is_none(Mt)

		Mt.Z = Z
		Mt.Y = Y
		self._correct_shape(Mt)
		self._correct_shape(M)

		Mt.clear_training_data()
		self._is_none(Mt)

	"""
	Test GP surrogate
	"""
	def test_gp_surrogate (self):
		Mt = GPModel(d)
		Mt.set_training_data(Z, Y)
		# Initialised as None
		assert Mt.gps is None

		# Set up GP surrogate
		Mt.gp_surrogate(kern_x = RBF, kern_p = RBF)
		assert len( Mt.gps ) == 2 # Number of outputs
		for gps in Mt.gps:
			assert len( gps ) == 1 # Number of binary variables
			assert isinstance( gps[0], GPRegression )

		# GP noise variance
		assert isinstance( Mt.gp_noise_var, float)

		# Hyperparameters
		assert Mt.hyp is None
		hyps  = [[ (i + 0.1) * (j + 0.5) * gp[:] for j,gp in enumerate(gps)] \
					for i,gps in enumerate(Mt.gps)]
		Mt.hyp = hyps
		assert Mt.hyp is not None

		Mt.gp_load_hyp()
		for hyp, gps in zip( hyps, Mt.gps ):
			for h, gp in zip( hyp, gps ):
				assert np.all( h == gp[:] )

		Mt.pmean = np.array([3., 4.])
		M,S = Mt.predict(Xs)
		assert M.shape == (len(Xs),2)
		assert S.shape == (len(Xs),2)



	"""
	Marginal surrogate
	"""
	def test_gprm (self):
		p = np.array([3., 4.])

		Mt = GPModel(d)
		Mt.pmean = np.array([3., 4.])
		assert Mt.gprm is None
		Mt.gp_surrogate(Z=Z, Y=Y, kern_x=RBF, kern_p=RBF)
		Mt.marginal_init_and_compute_covar(TaylorFirstOrder, Xs)
		M,S = Mt.marginal_predict(Xs)
		assert M.shape == (len(Xs),2)
		assert S.shape == (len(Xs),2,2)

		# Clear surrogate model
		Mt.clear_surrogate_model()
		assert Mt.Z is None
		assert Mt.Y is None
		assert Mt.gps is None
		assert Mt.hyp is None
		assert Mt.gprm is None


	"""
	Test dictionary
	"""
	def test_dict (self):
		d = M._get_save_dict()
		assert isinstance(d,dict)
		assert np.all( np.abs(d['Y'] - Y) <= 1e-10 )
		assert np.all( np.abs(d['Z'] - Z) <= 1e-10 )


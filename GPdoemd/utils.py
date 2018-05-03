
import numpy as np

def binary_dimensions (Z, binary_variables):
	"""
	Inputs
		Z 					Array of design variables (+ parameter (optional))
		binary_variables 	List of indices for binary design variables

	Outputs
		Range ( len( binary_variables ) )
		Column indices for non-binary variables (+ parameters)
		Row indices for different binary variables
	"""
	lb = len( binary_variables )

	if lb == 0:
		n1, n2 = Z.shape
		return [0], np.ones(n2,dtype=bool), np.zeros(n1)

	B = np.meshgrid( *( [[-1, 1]] * lb ) )
	B = np.vstack( map( np.ravel, B) ).T

	I  = range( Z.shape[1] )
	I  = [ i for i in I if not i in binary_variables ]

	Zt = Z[:, binary_variables] - 0.5
	J  = []
	for z in Zt:
		for j, b in enumerate(B):
			if np.all(b * z > 0):
				J.append(j)
				break
	return range( 2**lb ), np.array(I), np.array(J)


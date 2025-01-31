from jax import random
from jax import numpy as jnp
import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp

tfd = tfp.distributions 
from jsl.lds.kalman_filter import LDS, kalman_filter

import pytest

class TestKalmanFilters():
    # Utility functions
    def tfp_filter(self, timesteps, A, transition_noise_scale, C, observation_noise_scale, mu0, x_hist):
        state_size, _ = A.shape
        observation_size, _ = C.shape
        transition_noise = tfd.MultivariateNormalDiag(
            scale_diag=jnp.ones(state_size) * transition_noise_scale
        )
        obs_noise = tfd.MultivariateNormalDiag(
            scale_diag=jnp.ones(observation_size) * observation_noise_scale
        )
        prior = tfd.MultivariateNormalDiag(mu0, tf.ones([state_size]))

        LGSSM = tfd.LinearGaussianStateSpaceModel(
            timesteps, A, transition_noise, C, obs_noise, prior
        )

        _, filtered_means, filtered_covs, _, _, _, _ = LGSSM.forward_filter(x_hist)
        return jnp.array(filtered_means.numpy()), jnp.array(filtered_covs.numpy())
    
    def LDS_instance(self, timesteps, A, C, Q, R, mu0, Sigma0):
        return LDS(A, C, Q, R, mu0, Sigma0)

    def jsl_filter(self, lds_instance, x_hist):
        JSL_z_filt, JSL_Sigma_filt, _, _ = kalman_filter(lds_instance, x_hist)
        return JSL_z_filt, JSL_Sigma_filt
    
    def test_kalman_filter(self):
        timesteps = 15
        key = random.PRNGKey(0)
        observation_noise_scale = 1.0
        transition_noise_scale = 1.0
        
        A = jnp.eye(2)
        C = jnp.eye(2)

        Q = jnp.eye(2) * transition_noise_scale
        R = jnp.eye(2) * observation_noise_scale

        mu0 = jnp.array([5.0, 5.0])
        Sigma0 = jnp.eye(2) * 1.0

        lds = self.LDS_instance(timesteps, A, C, Q, R, mu0, Sigma0)

        z_hist, x_hist = lds.sample(key, timesteps)

        # run tfp filtering
        tfp_filtered_means, tfp_filtered_covs = self.tfp_filter(timesteps, A, transition_noise_scale, C, observation_noise_scale, mu0, x_hist)

        # run jsl_filtering
        jsl_filtered_means, jsl_filtered_covs = self.jsl_filter(lds, x_hist)

        # Assert statements
        assert jnp.allclose(jsl_filtered_means, tfp_filtered_means, rtol=1e-2)
        assert jnp.allclose(jsl_filtered_covs, tfp_filtered_covs, rtol=1e-2)

import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import tensorflow as tf
import numpy as np
import h5py

print("🔄 Initializing C.A.R.E. Engine Conversion Architecture...")

# Rebuilt model layout using 3 channels (RGB) to match Mohamed Ali's trained shape exactly
def build_native_care_architecture():
    # Notice the 3 at the end instead of 1
    inputs = tf.keras.Input(shape=(240, 240, 3))
    
    # Block 1
    x = tf.keras.layers.ZeroPadding2D(padding=(2, 2))(inputs)
    x = tf.keras.layers.Conv2D(32, kernel_size=(7, 7), strides=(1, 1), name='conv0')(x)
    x = tf.keras.layers.BatchNormalization(axis=3, name='bn0')(x)
    x = tf.keras.layers.Activation('relu')(x)
    x = tf.keras.layers.MaxPooling2D(pool_size=(4, 4), name='max_pool0')(x)
    
    # Block 2
    x = tf.keras.layers.MaxPooling2D(pool_size=(4, 4), name='max_pool1')(x)
    
    # Output Classification Layers
    x = tf.keras.layers.Flatten()(x)
    outputs = tf.keras.layers.Dense(1, activation='sigmoid', name='fc')(x)
    
    return tf.keras.Model(inputs=inputs, outputs=outputs)

try:
    print("📂 Extracting internal legacy synaptic weights...")
    legacy_path = 'models/cnn-parameters-improvement-23-0.91.model'
    
    # Initialize our native structural model template
    native_model = build_native_care_architecture()
    
    # Map layers directly using h5py parameters
    with h5py.File(legacy_path, 'r') as f:
        # Map Conv0 Layer
        c0_w = f['model_weights']['conv0']['conv0']['kernel:0'][:]
        c0_b = f['model_weights']['conv0']['conv0']['bias:0'][:]
        native_model.get_layer('conv0').set_weights([c0_w, c0_b])
        
        # Map Batch Normalization Layer
        bn_beta = f['model_weights']['bn0']['bn0']['beta:0'][:]
        bn_gamma = f['model_weights']['bn0']['bn0']['gamma:0'][:]
        bn_mean = f['model_weights']['bn0']['bn0']['moving_mean:0'][:]
        bn_var = f['model_weights']['bn0']['bn0']['moving_variance:0'][:]
        native_model.get_layer('bn0').set_weights([bn_gamma, bn_beta, bn_mean, bn_var])
        
        # Map Fully Connected Output Layer
        fc_w = f['model_weights']['fc']['fc']['kernel:0'][:]
        fc_b = f['model_weights']['fc']['fc']['bias:0'][:]
        native_model.get_layer('fc').set_weights([fc_w, fc_b])

    # Save cleanly as modern Keras format
    native_model.save('models/care_keras3_model.keras')
    print("✅ Success! 'models/care_keras3_model.keras' successfully generated with matching parameters.")

except Exception as e:
    print(f"⚠️ Manual extraction structural mismatch: {e}")

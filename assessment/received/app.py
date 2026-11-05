import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
import time
import h5py
import os

# 1. Page Config Setup
st.set_page_config(
    page_title="C.A.R.E. Diagnostics Engine",
    page_icon="🧠",
    layout="wide"
)

# Dark Tech Cyber Theme Customization
st.markdown("""
    <style>
    .main { background-color: #060913; color: #e2e8f0; }
    .stApp { background: radial-gradient(circle at 50% 50%, #0d1527 0%, #070a12 100%); }
    h1 { color: #00f0ff; font-family: 'Courier New', monospace; text-align: center; text-shadow: 0 0 10px #00f0ff; font-weight: 800; }
    .brand-sub { text-align: center; color: #39b5ff; font-family: sans-serif; font-weight: bold; letter-spacing: 2px; margin-bottom: 25px; }
    .status-card { background-color: #0b1120; border: 1px solid #1e293b; padding: 20px; border-radius: 12px; }
    div.stButton > button {
        background-color: #0b1120; color: #39b5ff; border: 1px solid #1e293b; 
        border-radius: 8px; width: 100%; transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #00f0ff; color: #00f0ff; box-shadow: 0 0 10px rgba(0,240,255,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Model Architecture Assembly & Direct Weight Mapping
@st.cache_resource
def load_care_model_safely():
    inputs = tf.keras.Input(shape=(240, 240, 3))
    x = tf.keras.layers.ZeroPadding2D(padding=(2, 2))(inputs)
    x = tf.keras.layers.Conv2D(32, kernel_size=(7, 7), strides=(1, 1), name='conv0')(x)
    x = tf.keras.layers.BatchNormalization(axis=3, name='bn0')(x)
    x = tf.keras.layers.Activation('relu')(x)
    x = tf.keras.layers.MaxPooling2D(pool_size=(4, 4), name='max_pool0')(x)
    x = tf.keras.layers.MaxPooling2D(pool_size=(4, 4), name='max_pool1')(x)
    x = tf.keras.layers.Flatten()(x)
    outputs = tf.keras.layers.Dense(1, activation='sigmoid', name='fc')(x)
    native_model = tf.keras.Model(inputs=inputs, outputs=outputs)
    
    legacy_path = 'models/cnn-parameters-improvement-23-0.91.model'
    with h5py.File(legacy_path, 'r') as f:
        c0_w = f['model_weights']['conv0']['conv0']['kernel:0'][:]
        c0_b = f['model_weights']['conv0']['conv0']['bias:0'][:]
        native_model.get_layer('conv0').set_weights([c0_w, c0_b])
        
        bn_beta = f['model_weights']['bn0']['bn0']['beta:0'][:]
        bn_gamma = f['model_weights']['bn0']['bn0']['gamma:0'][:]
        bn_mean = f['model_weights']['bn0']['bn0']['moving_mean:0'][:]
        bn_var = f['model_weights']['bn0']['bn0']['moving_variance:0'][:]
        native_model.get_layer('bn0').set_weights([bn_gamma, bn_beta, bn_mean, bn_var])
        
        fc_w = f['model_weights']['fc']['fc']['kernel:0'][:]
        fc_b = f['model_weights']['fc']['fc']['bias:0'][:]
        native_model.get_layer('fc').set_weights([fc_w, fc_b])
        
    return native_model

model_loaded = False
try:
    model = load_care_model_safely()
    model_loaded = True
except Exception as e:
    st.error(f"⚠️ C.A.R.E. Core Failure: Direct parameter extraction failed. Error Details: {e}")

# 3. Branding Header
st.markdown("<h1>C.A.R.E. DIAGNOSTICS Suite</h1>", unsafe_allow_html=True)
st.markdown("<div class='brand-sub'>CEREBRAL ANOMALY RADIOLOGY EVALUATION</div>", unsafe_allow_html=True)
st.divider()

if model_loaded:
    st.success("📡 C.A.R.E. Diagnostics System Online: Connected to Neural Matrix")
    
    # Left Column: Image Inputs & Samples | Right Column: Live Analysis Engine
    left_ui, right_ui = st.columns(2, gap="large")
    
    # Initialize session state tracking variable for target images
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None

    with left_ui:
        st.markdown("### 🖥️ Neuro-Imaging Input Window")
        
        # Accessibility Sample System Grid Setup
        st.write("📋 **Quick-Load Preset Patient Scans:**")
        s_col1, s_col2 = st.columns(2)
        
        with s_col1:
            if st.button("🧬 Load Sample Alpha (Tumor)"):
                # Dynamically maps path arrays directly from original repository folder
                if os.path.exists("yes/Y1.jpg"):
                    st.session_state.selected_image = "yes/Y1.jpg"
                elif os.walk("yes"):
                    for root, dirs, files in os.walk("yes"):
                        if files: st.session_state.selected_image = os.path.join(root, files[0])
        
        with s_col2:
            if st.button("✅ Load Sample Beta (Healthy)"):
                if os.path.exists("no/1 no.jpeg"):
                    st.session_state.selected_image = "no/1 no.jpeg"
                elif os.walk("no"):
                    for root, dirs, files in os.walk("no"):
                        if files: st.session_state.selected_image = os.path.join(root, files[0])
                        
        st.write("---")
        
        # Standard External Manual Upload Widget Box
        uploaded_file = st.file_uploader("Or feed an external patient scan into the engine...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            st.session_state.selected_image = uploaded_file

        # Display the active focus target frame image
        if st.session_state.selected_image is not None:
            image = Image.open(st.session_state.selected_image)
            st.image(image, caption='Active Target Diagnostic Frame Scan', use_container_width=True)
            
    with right_ui:
        st.markdown("### ⚡ Neural Processing Matrix")
        
        if st.session_state.selected_image is not None:
            progress_bar = st.progress(0)
            st_text = st.empty()
            
            for stage in range(100):
                time.sleep(0.002)
                progress_bar.progress(stage + 1)
                if stage < 45:
                    st_text.code("⏳ STATUS: Truncating black background skull margins...")
                elif stage < 80:
                    st_text.code("🧬 STATUS: Deploying Convolutional Neural Filters [3 Channel RGB Mode]...")
                else:
                    st_text.code("🧠 STATUS: Querying dense connected classification layer...")
            
            st_text.code("✅ STATUS: Neural mapping evaluation finished.")
            
            # --- COMPUTER VISION PREPROCESSING FRAME PIPELINE ---
            open_cv_image = np.array(image.convert('RGB')) 
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[0] if len(cnts) > 0 else []
            
            if len(cnts) > 0:
                c = max(cnts, key=cv2.contourArea)
                extLeft = int(c[c[:, :, 0].argmin()][0][0])
                extRight = int(c[c[:, :, 0].argmax()][0][0])
                extTop = int(c[c[:, :, 1].argmin()][0][1])
                extBot = int(c[c[:, :, 1].argmax()][0][1])
                if extBot > extTop and extRight > extLeft:
                    open_cv_image = open_cv_image[extTop:extBot, extLeft:extRight]
            
            img_resized = cv2.resize(open_cv_image, (240, 240))
            img_normalized = img_resized / 255.0
            img_reshaped = np.reshape(img_normalized, (1, 240, 240, 3))
            
            # Execution Prediction Evaluation
            prediction_matrix = model.predict(img_reshaped)
            confidence_val = float(prediction_matrix[0][0])
            
            st.markdown("<div class='status-card'>", unsafe_allow_html=True)
            st.markdown("### 📊 Diagnostic Output Matrix:")
            
            if confidence_val > 0.5:
                st.markdown("<h2 style='color: #ff3366; text-shadow: 0 0 10px #ff3366;'>⚠️ POSITIVE PATHOLOGY INDICATION</h2>", unsafe_allow_html=True)
                st.info(f"**C.A.R.E. Confidence:** {confidence_val*100:.2f}% probability of abnormal tissue mass presence.")
            else:
                st.markdown("<h2 style='color: #00ff66; text-shadow: 0 0 10px #00ff66;'>✅ NEGATIVE PATHOLOGY INDICATION</h2>", unsafe_allow_html=True)
                st.info(f"**C.A.R.E. Confidence:** {(1-confidence_val)*100:.2f}% probability of standard healthy scan bounds.")
            st.markdown("</div>", unsafe_allow_html=True)

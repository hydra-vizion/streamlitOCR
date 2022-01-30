from distutils.command.config import config
import streamlit as st
import pandas as pd
import cv2
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pytesseract

# pytesseract.pytesseract.tesseract_cmd = r'B:\Tesseract4\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = './Tesseract4/tesseract.exe'
st.header("Upload receipt picture")
st.write("Upload receipt picture")

uploaded_file = st.file_uploader("Choose an image...")

image = ''
def rusn(img):
    # blur = cv2.GaussianBlur(uploaded_file,(9,9),0)
    # output = Image.fromarray(uploaded_file)
    # output.save('grayori.png')
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return image

if uploaded_file:
    image = Image.open(uploaded_file)
    image = np.array(image)
    st.image(image)

# input_data = st.text_area("input")
# parsed_data = "a" # Some function you've made to clean the input data

# allow_editing = st.radio("Edit parsed data", [True, False])

# if allow_editing:
#     output = st.text_area("parsed data", value=parsed_data)
# else:
#     st.text(parsed_data)
    

options = "--psm 11"
import time

ocr = st.button(label="OCR Image")
placeholder = st.empty()

dates = "2/12/22"
months = dates.split('/')[2]
st.write(months)

if ocr:
    if uploaded_file:
        placeholder.text("Loading....OCR")
        image = Image.open(uploaded_file)
        image = np.array(image)
        image = rusn(image)
        extracted_text6 = pytesseract.image_to_string(image,config=options)
        st.write(extracted_text6)
        placeholder.empty()
    else:
        st.write("Please upload receipt picture")



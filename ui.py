from distutils.command.config import config
from nltk.util import pr
import streamlit as st
import pandas as pd
import cv2
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
from dateutil import parser
from jellyfish import jaro_distance as jd
import nltk
import re
import pandas as pd


# pytesseract.pytesseract.tesseract_cmd = r'B:\Tesseract4\tesseract.exe'

st.set_page_config(layout="wide",page_title="Receipt OCR to CSV for Expenditure analysis")
col1,col2,col4,col3= st.columns((1,3,1,1))
matcher = pd.DataFrame(columns={"ds","y"})
if 'count' not in st.session_state:
    st.session_state.count = pd.DataFrame(columns={"ds","y"})
    st.session_state.canSave = False
    st.session_state.spend = 0
    st.session_state.date = ""



def start():
    col2.header("Receipt OCR to CSV for Expenditure analysis")
    col2.write("Upload receipt picture")
    uploaded_file = col2.file_uploader("Choose an image...",type=['png', 'jpg','jpeg'])
    image = ''

    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            image = np.array(image)
            col2.image(image,width=250)
        except:
            if st.session_state.canSave:
                col2.write("Press Save again to confirm")
            else:
                col2.write("File can't be read, it is either unsupported or corrupted file type. Please upload new file (PNG, JPG, JPEG)")
    
    ocr = col2.button(label="OCR Image")
    placeholder = col2.empty()
    if ocr:
        if uploaded_file:
            
            placeholder.text("Loading OCR.... Please Wait")
            image = Image.open(uploaded_file)
            image = np.array(image)
            image = retImg(image)
            
            find_All(image)
            # st.write(extracted_text)
            placeholder.empty()
            st.session_state.canSave =True
            
        else:
            col2.write("Please upload receipt picture")
    saveDatas = 0
    if st.session_state.canSave:
        # Show in UI
        col2.write("Are you sure this information is correct?")
        spendsinput = col2.text_input("Spending", value=st.session_state.spend)
        dateinput = col2.text_input("Date", value=st.session_state.date)
        saveDatas = col2.button(label="Save")
        
    if saveDatas and st.session_state.canSave:
        if not checkDateFormat(dateinput):
            col2.write("Check the date format, only input numbers Eg. dd/mm/yyyy, 10/1/2022, 10,1,22")
        elif not checkSpendType(spendsinput):
            col2.write("Only input numbers or decimals")
        else:
            st.session_state.count = addtoDataFrame(st.session_state.count,dateinput,spendsinput)
            st.session_state.canSave = False
            col2.write("Data saved into CSV (last row), Press save again to sort")
        

    if not st.session_state.count.empty:
        col3.write("Saved data in CSV format")
        col3.dataframe(st.session_state.count)
        dFram = st.session_state.count
        dFram["ds"] = pd.to_datetime(dFram["ds"],dayfirst=True)
        dFram["ds"] = dFram["ds"].dt.strftime("%Y/%m/%d")
        dFram = dFram.sort_values(by=['ds'])
        dFram.reset_index(inplace=True,drop=True)
        dFram["ds"] = pd.to_datetime(dFram["ds"],yearfirst=True,dayfirst=False)
        dFram["ds"] = dFram["ds"].dt.strftime("%d/%m/%Y")
        st.session_state.count = dFram
        dFram = dFram.to_csv(index=False).encode('utf-8')
        dload = col3.download_button("Download CSV",dFram,"data.csv","text/csv",key='download-csv')

# def changeDatetoNormal(date):

def checkDateFormat(date):
    dateSplit = date.split('/')
    for i in range(len(dateSplit)):
        if not dateSplit[i].isdigit():
            return False
    return True   
    
def checkSpendType(spend):
    try:
        float(spend)
        return True
    except:
        return False

# grayscaled image
def retImg(img):
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return image

# apply CLAHE to image
def hist_eql(img):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cla = clahe.apply(img)
    return cla

# apply gaussian blur to image
def gaussblur(img):
    blur = cv2.GaussianBlur(img,(5,5),0)
    return blur

# apply sharpening to image
def sharpen(img):
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharp = cv2.filter2D(img, -1, kernel)
    return sharp

# binarize image
def binarize(img):
    thresh = 125 #higher value for darker result
    bin_image = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY)[1]
    return bin_image

def pass1(img):
    claheImg = hist_eql(img)
    result = binarize(claheImg)
    return result

def pass2(img):
    blurImg = gaussblur(img)
    sharpImg = sharpen(blurImg)
    result = binarize(sharpImg)
    return result   

# add date and spend to DF
def addtoDataFrame(dataF,date,spends):
    dataF = dataF.append({"ds":date,"y":spends}, ignore_index=True)
    return dataF

# init database
def createDataFrame():
    df = pd.DataFrame(columns={"ds","y"})
    return df

# downcasing all text in array
def downcase(list):
    for i in range(len(list)):
        if not list[i].isdigit():
            list[i] = list[i].lower()
    return list

def normalize(text):
    # tokenize extracted words
    token = nltk.word_tokenize(text)
    words = [word for word in token if len(word) > 2]
    words = downcase(words)
    return words

# find spending value after found total/amount text(prototype) //using text strings
def find_spending(text):
    # tokenize extracted words
    token = normalize(text)
    # remove word below 2 characters 
    # words = [word for word in token if len(word) > 2]
    words = token
    # find total/subtotal/amount if jaro>0.8
    pos = -1;
    for i in range(len(words)):
        if jd(words[i],'subtotal') > 0.88:
            pos = i + 1
            break
        else:
            pos = -1
    if pos == -1:
        for i in range(len(words)):
            if jd(words[i],'total') > 0.8:
                pos = i + 1
                break
            elif jd(words[i],'amount') > 0.8:
                pos = i + 1
                break
            else:
                pos = -1 
    if pos == -1:
        return [0]

    
    # find next number in array after total/amount
    spends = []
    itr = len(words)-pos
        # iterate for every text in string after total/amount
    for i in range(itr):
        spends.append(words[pos+i])
    text_string = ''.join(spends)
    amounts = re.findall(r'(\d+\.\d+)', text_string)

    if amounts == []:
        return [0]
    floats = [float("%.2f" % float(amount)) for amount in amounts]
    # unique = list(dict.fromkeys(floats))
    # unique = most_frequent(list(dict.fromkeys(floats)))
    
    return floats

# find date if not return -1 //using text strings
def find_date(text):
    
    # find date with xx/xx/xx
    try:
        match = re.search(r'(\d+/\d+/\d+)',text)
        datefound = match.group(1)
    except:
        # find date with xx-xx-xx
        try:
            match = re.search(r'(\d+-\d+-\d+)',text)
            datefound = match.group(1)
        # return 0 if date is not found
        except:
            datefound = -1
    
    return datefound

def find_All(image):
    p1image = pass1(image)
    p2image = pass2(image)
    binimage = binarize(image)
    blurimage = gaussblur(image)
    options = "--psm 11"
    graytxt = pytesseract.image_to_string(image,config=options)
    p1txt = pytesseract.image_to_string(p1image,config=options)
    p2txt = pytesseract.image_to_string(p2image,config=options)
    bintxt = pytesseract.image_to_string(binimage,config=options)
    blurtxt = pytesseract.image_to_string(blurimage,config=options)

    spendgray = find_spending(graytxt)
    spendp1 = find_spending(p1txt)
    spendp2 = find_spending(p2txt)
    spendbin = find_spending(bintxt)
    spendblur = find_spending(blurtxt)
    
    # reduce all possible spend finding in the array and find most frequent number
    finalSpend = spendgray + spendp1 + spendp2 + spendbin +spendblur
    finalSpend = [a for a in finalSpend if a > 1.0]
    if finalSpend == []:
        finalSpend = 0
    else:    
        finalSpend = most_frequent(finalSpend)
    
    # reduce all possible date finding
    datesFound = [find_date(graytxt), find_date(p1txt), find_date(p2txt), find_date(bintxt), find_date(blurtxt)]
    datesFound = [a for a in datesFound if a != -1]
    if datesFound == []:
        finalDate = "dd/mm/yy (Date not Found)"
    else:    
        finalDate = normalize_date(datesFound)

    # Store in memory
    st.session_state.spend = finalSpend
    st.session_state.date = finalDate

    

    # saveData = col2.button(label="save")
    # if saveData:
    #     dFrame = st.session_state.count
    #     dFrame = addtoDataFrame(dFrame,dateinput,spendsinput)
    #     st.session_state.count = dFrame
       

        
    
    
def normalize_date(datesArr):
    day = []
    month = []
    year = []

    for i in range(len(datesArr)):
        dateSplit = datesArr[i].split('/')
        day.append(dateSplit[0])
        month.append(dateSplit[1])
        year.append(dateSplit[2])
    
    day = [int(d) for d in day if int(d) < 32]
    month = [int(m) for m in month if int(m) < 13]
    year = [int(y) for y in year if int(y) < 2050]

    dayFreq = most_frequent(day)
    monthFreq = most_frequent(month)
    yearFreq = most_frequent(year)

    dateToReturn = "{}/{}/{}".format(dayFreq,monthFreq,yearFreq)
    return dateToReturn


def most_frequent(List):
    return max(set(List), key = List.count)




start()
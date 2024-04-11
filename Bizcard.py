import streamlit as st
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import re
import io

#connecting to mysql
import mysql.connector
connection=mysql.connector.connect(       
                host='localhost',
                user='root',
                password='12345678',
                database='BizCard_Project')
cursor=connection.cursor()

#extracting text and image

def image_to_text(path):
    input_image= Image.open(path)
    image_array= np.array(input_image) #converting image to array format
    reader= easyocr.Reader(['en']) #read data in english language
    text=reader.readtext(image_array,detail=0) # 0 means only text data
    return text, input_image

def extracted_text(texts):
    extracted_dict={"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"CONTACT":[],"EMAIL":[],"WEBSITE":[],"ADDRESS":[],"PINCODE":[]}
    extracted_dict["NAME"].append(texts[0])
    extracted_dict["DESIGNATION"].append(texts[1])
    for i in range(2,len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):
            extracted_dict["CONTACT"].append(texts[i])
        elif "@" in texts[i] and ".com" in texts[i]:
            extracted_dict["EMAIL"].append(texts[i])
        elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
            small=texts[i].lower()
            extracted_dict["WEBSITE"].append(small)
        elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
            extracted_dict["PINCODE"].append(texts[i])
        elif re.match(r'^[A-Za-z]',texts[i]):
            extracted_dict["COMPANY_NAME"].append(texts[i])
        else:
            remove_colon= re.sub(r'[,;]','',texts[i])
            extracted_dict["ADDRESS"].append(remove_colon)
    for key,value in extracted_dict.items():
         if len(value)>0:
             concatenate=" ".join(value)
             extracted_dict[key]=[concatenate]
         else:
            value="NA"
            extracted_dict[key]=[value]

    return extracted_dict

#streamlit part

st.set_page_config(layout="wide")
st.title("**BizCardX: Extracting Business Card Data with OCR**")

with st.sidebar:
    select= option_menu("Main Menu",["Home","Upload & Modify","Delete"])
if select=="Home":
    st.markdown(":blue[**BizCard application is used for extracting the information from the business cards. It helps in collecting the necessary information using different technologies and stores in database thereby reducing time & efforts spent on manual data entry.**]")
    st.subheader(":rainbow[**Technologies Used in Extraction**]")
    st.write(":green[1.**Python**]")
    st.write(":green[2.**EasyOCR**]")
    st.write(":green[3.**Pandas**]")
    st.write(":green[4.**Streamlit**]")
    st.write(":green[5.**SQL**]")
elif select=="Upload & Modify":
    image= st.file_uploader("Upload the Image", type=["png","jpg","jpeg"])
    
    if image is not None:
        st.image(image,width=300)
        
        text_image,input_image=image_to_text(image)
        
        text_dict=extracted_text(text_image)
        
        if text_dict:
            st.success("Text is Extracted Successfully")
            
        df=pd.DataFrame(text_dict)
        
        #Converting Image to Bytes
        Image_bytes= io.BytesIO()
        input_image.save(Image_bytes,format="PNG")
        image_data=Image_bytes.getvalue()
        
        #Creating Dictionary
        data={"IMAGE":[image_data]}
        
        df1=pd.DataFrame(data)
        
        concat_df = pd.concat([df,df1],axis=1)
        st.dataframe(concat_df)

        button1=st.button("Save")
        if button1:
            #SQL table creation and insertion
            Create_table= '''Create TABLE IF NOT EXISTS Bizcard_Info(Name varchar(255),
                                                                      Designation varchar(255),
                                                                      Company_Name varchar(255),
                                                                      Contact varchar(255),
                                                                      Email varchar(255),
                                                                      Website text,
                                                                      Address text,
                                                                      Pincode varchar(255),
                                                                      Image LONGBLOB
                                                                      )'''
            cursor.execute(Create_table)
            # insert 
            insert_query = '''INSERT INTO Bizcard_Info(Name,Designation,Company_Name,Contact,Email,Website,Address,Pincode,Image)
                           values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            data= concat_df.values.tolist()[0]
            cursor.execute(insert_query,data)
            connection.commit()
            st.success("Details saved successfully")
        method=st.radio("Select the method",["Preview","Modify"])
        #if method=="None":
            #st.write("")
        if method=="Preview":
            #gets the data from db
            Query2= "Select * from Bizcard_Info"
            cursor.execute(Query2)
            Table=cursor.fetchall()
            df=pd.DataFrame(Table,columns=("Name","Designation","Company_Name","Contact","Email","Website","Address","Pincode","Image"))
            st.dataframe(df)
        elif method=="Modify":
            Query2= "Select * from Bizcard_Info"
            cursor.execute(Query2)
            Table=cursor.fetchall()
            df=pd.DataFrame(Table,columns=("Name","Designation","Company_Name","Contact","Email","Website","Address","Pincode","Image"))
            col1,col2= st.columns(2)
            with col1:
                Selected_name= st.selectbox("Select the name",df["Name"])
            df_1= df[df["Name"]==Selected_name]
            st.dataframe(df_1)
            df_2= df_1.copy()
            col1,col2=st.columns(2)
            with col1:
                m_name=st.text_input("Name",df_1["Name"].unique()[0])
                m_designation=st.text_input("Designation",df_1["Designation"].unique()[0])
                m_Companyname=st.text_input("Company_Name",df_1["Company_Name"].unique()[0])
                m_Contact=st.text_input("Contact",df_1["Contact"].unique()[0])
                m_Email=st.text_input("Email",df_1["Email"].unique()[0])
                df_2["Name"]=m_name
                df_2["Designation"]=m_designation
                df_2["Company_Name"]=m_Companyname
                df_2["Contact"]=m_Contact
                df_2["Email"]=m_Email
            with col2:
                m_Website=st.text_input("Website",df_1["Website"].unique()[0])
                m_Address=st.text_input("Address",df_1["Address"].unique()[0])
                m_Pincode=st.text_input("Pincode",df_1["Pincode"].unique()[0])
                m_Image=st.text_input("Image",df_1["Image"].unique()[0])
                df_2["Website"]=m_Website
                df_2["Address"]=m_Address
                df_2["Pincode"]=m_Pincode
                df_2["Image"]=m_Image
            st.dataframe(df_2)
            col1,col2=st.columns(2)
            with col1:
                button2=st.button("Modify")
            if button2:
                cursor.execute(f"DELETE FROM Bizcard_Info WHERE NAME='{Selected_name}'")
                connection.commit()
                insert_query = '''INSERT INTO Bizcard_Info(Name,Designation,Company_Name,Contact,Email,Website,Address,Pincode,Image)
                           values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                data= df_2.values.tolist()[0]
                cursor.execute(insert_query,data)
                connection.commit()
                st.success("Modified data successfully")
                

    
elif select=="Delete":
    col1,col2=st.columns(2)
    with col1:
        select_query="SELECT Name FROM Bizcard_Info"
        cursor.execute(select_query)
        table=cursor.fetchall()
        names=[]
        for i in table:
            names.append(i[0])
        selected_name=st.selectbox("Select the name",names)
    with col2:
        select_query=f"SELECT Designation FROM Bizcard_Info WHERE Name ='{selected_name}'"
        cursor.execute(select_query)
        table=cursor.fetchall()
        designation=[]
        for j in table:
            designation.append(j[0])
        selected_designation=st.selectbox("Select the designation",designation)
    if selected_name and selected_designation:
        col1,col2=st.columns(2)
        with col1:
            st.write(f"Selected Name: {selected_name}")
            st.write("")
            st.write(f"Selected Designation: {selected_designation}")
        with col2:
            st.write("")
            st.write("")
            st.write("")
            remove=st.button("Delete")
            if remove:
                cursor.execute(f"DELETE FROM Bizcard_Info WHERE Name='{selected_name}' AND Designation='{selected_designation}'")
                connection.commit()
                st.warning("DELETED")
        
            
            
        




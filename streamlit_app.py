# import packages

# streamlit for the app
import streamlit as st 

# pandas for.. well its pandas!
import pandas as pd

# see above
import numpy as np

# plottin and graphin
import matplotlib.pyplot as plt


# streamlit app code all goes in here
def main():

    # app title
    st.title("Secret Key App")

    # create 'enter key' box
    secret_key = st.text_input("Enter the secret key:")

    # if the key is correct
    if secret_key == 'ANIMALS':
        st.write('Hello')

        y = np.array([35, 25, 25, 15])

        plt.pie(y)
        st.pyplot()




    # if the key is incorrect
    else:
        st.warning("Incorrect key!")


# to run the streamlit app 
if __name__ == "__main__":
    main()

    st
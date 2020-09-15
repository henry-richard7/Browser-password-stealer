import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import datetime
import PySimpleGUI as sg

FileName = 116444736000000000
NanoSeconds = 10000000


def ConvertDate(ft):
    utc = datetime.utcfromtimestamp(((10 * int(ft)) - FileName) / NanoSeconds)
    return utc.strftime('%Y-%m-%d %H:%M:%S')


def get_master_key():
    try:
     with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State',
              "r", encoding='utf-8') as f:
        local_state = f.read()
        local_state = json.loads(local_state)
    except:
        sg.popup("Error","Chrome Not Installed")
        exit()
    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    master_key = master_key[5:]  # removing DPAPI
    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
    return master_key


def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)


def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)


def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = generate_cipher(master_key, iv)
        decrypted_pass = decrypt_payload(cipher, payload)
        decrypted_pass = decrypted_pass[:-16].decode()  # remove suffix bytes
        return decrypted_pass
    except Exception as e:
        return "Chrome < 80"


def get_password():
    master_key = get_master_key()
    login_db = os.environ[
                   'USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\default\Login Data'
    try:
        shutil.copy2(login_db,
                     "Loginvault.db")  # making a temp copy since Login Data DB is locked while Chrome is running
    except:
        print("[*] Brave Browser Not Installed !!")
    conn = sqlite3.connect("Loginvault.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        for r in cursor.fetchall():
            url = r[0]
            username = r[1]
            encrypted_password = r[2]
            decrypted_password = decrypt_password(encrypted_password, master_key)
            if username != "" or decrypted_password != "":
                window['Saved_Passwords'].print(
                    "URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n" + "*" * 10 + "\n")
    except Exception as e:
        pass

    cursor.close()
    conn.close()
    try:
        os.remove("Loginvault.db")
    except Exception as e:
        pass


def get_credit_cards():
    master_key = get_master_key()
    login_db = os.environ[
                   'USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\default\Web Data'
    shutil.copy2(login_db,
                     "CCvault.db")  # making a temp copy since Login Data DB is locked while Chrome is running
    conn = sqlite3.connect("CCvault.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM credit_cards")
        for r in cursor.fetchall():
            username = r[1]
            encrypted_password = r[4]
            decrypted_password = decrypt_password(encrypted_password, master_key)
            expire_mon = r[2]
            expire_year = r[3]
            window['Saved_CCs'].print(
                "Name in Card: " + username + "\nNumber: " + decrypted_password + "\nExpire Month: " + str(
                    expire_mon) + "\nExpire Year: " + str(expire_year) + "\n" + "*" * 10 + "\n")

    except Exception as e:
        pass

    cursor.close()
    conn.close()
    try:
        os.remove("CCvault.db")
    except Exception as e:
        pass


def get_bookmarks():
    bookmarks_location = os.environ[
                             'USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\default\Bookmarks'
    with open(bookmarks_location) as f:
        data = json.load(f)
        bookmarks_list = data["roots"]["bookmark_bar"]["children"]
        for i in range(len(bookmarks_list)):
            window['Bookmarks'].print(f"Name: {bookmarks_list[i]['name']}\n"
                                      f"Url: {bookmarks_list[i]['url']}\n"
                                      f"Added on: {ConvertDate(bookmarks_list[i]['date_added'])}\n")


sg.theme("DarkBlue")
Layout = [[sg.Image(filename="Icons/chrome.png", size=(50, 50)),
           sg.Text("Chrome Browser Saved Data Decrypter", font=("", 25))],
          [sg.Text("Developed by Henry Richard J", font=("", 15))],
          [sg.Multiline("Saved Passwords here", size=(45, 25), disabled=True, key="Saved_Passwords", font=("", 12),
                        text_color="white"),
           sg.Multiline("Saved Credit Cards here", size=(45, 25), disabled=True, key="Saved_CCs", font=("", 12),
                        text_color="white"),
           sg.Multiline("Bookmarks here", size=(45, 25), disabled=True, key="Bookmarks", font=("", 12),
                        text_color="white")],
          [sg.Button("Get Data", size=(15, 2), font=("", 15), key="get_data")]]

window = sg.Window('Chrome Decrypter', Layout, element_justification='center')

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

    if event == "get_data":
        window['Saved_Passwords'].update("")
        window['Saved_CCs'].update("")
        window['Bookmarks'].update("")

        get_password()
        get_credit_cards()
        get_bookmarks()

window.close()

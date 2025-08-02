''' 
Ask for state
Ask for District
Ask for Assembly Consitituency using sample code logic
Ask language
Roll types are static - check which ones in the sample code
Captcha using gemini api
Ask how many booths and for which number to which one or 'all' or just one
'''
import base64,os
import google.generativeai as genai
import requests
from io import BytesIO
from PIL import Image



def state_selection():
    response = requests.get("https://gateway-voters.eci.gov.in/api/v1/common/states")
    state_data = response.json()
    states = {}
    print("\nSelect State:")
    for i, state in enumerate(state_data):
        states[i+1] = (state['stateCd'],state['stateName'])
        print(f"{i+1} - {state['stateName']}")

    choice = int(input("Enter the number of your choice: "))
    if choice in states:
        state_choice,state_name = states[choice]
        return state_choice,state_name
def district_selection(state_id):
    response = requests.get(f"https://gateway-voters.eci.gov.in/api/v1/common/districts/{state_id}")
    district_data = response.json()
    districts = {}
    print("\nSelect District:")
    for i, district in enumerate(district_data):
        districts[i+1] = (district['districtCd'],district['districtValue'])
        print(f"{i+1} - {district['districtValue']}")

    choice = int(input("Enter the number of your choice: "))
    if choice in districts:
        district_id,district_name = districts[choice]
        return district_id,district_name

def assembly_selection(state_id, district_id):
    response = requests.get("https://gateway-voters.eci.gov.in/api/v1/common/constituencies",params={"stateCode":state_id})
    if response:
        filtered_assemblies = [
            a for a in response.json()
            if a.get('districtCd') == district_id
        ]
        assemblies = {}
        print("\nSelect Assembly:")
        for i, assembly in enumerate(filtered_assemblies):
            assemblies[i+1] = (assembly['asmblyNo'],assembly['asmblyName'])
            print(f"{i+1}. {assembly['asmblyName']}")

        choice = int(input("Enter the number of your choice: "))
        if choice in assemblies:
            assembly_id,assembly_name = assemblies[choice]
            return assembly_id,assembly_name
def language_selection(state_id, district_id, assembly_id):
    payload = {
        "stateCd": state_id,
        "districtCd": district_id,
        "acNumber": assembly_id,
        "pageNumber": 0,
        "pageSize": 10
    }
    response = requests.post("https://gateway-voters.eci.gov.in/api/v1/printing-publish/get-ac-languages", json=payload)
    if response and response.json().get('payload'):
        languages = {}
        print("\nSelect Language:")
        for i, (lang_id, lang_name) in enumerate(response.json()['payload'].items()):
            languages[i+1] = lang_id
            print(f"{i+1}. {lang_name}")

        choice = int(input("Enter the number of your choice: "))
        if choice in languages:
            language_id = languages[choice]
            return language_id


def download_and_solve_captcha():
    response = requests.get("https://gateway-voters.eci.gov.in/api/v1/captcha-service/generateCaptcha/EROLL")
    captcha_b64 = response.json()["captcha"]
    captcha_id = response.json()["id"]

    image_data = base64.b64decode(captcha_b64)
    image = Image.open(BytesIO(image_data))
    image.save("captcha.png")
    print("Saved image as captcha.png")

    genai.configure(api_key="API_KEY_HERE")
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = (
        "Read the text in this CAPTCHA image and return ONLY the exact 6 characters. There are exactly 6 characters and be aware that there is a diagonal line running. "
        "Do not add spaces or explanations. There are only digits and alphabets. No hypens or anythin"
    )

    resp = model.generate_content(
        [prompt, {"mime_type": "image/jpeg", "data": image_data}]
    )

    return captcha_id,resp.text

def get_pdf_parts():
    url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/get-part-list"
    payload = {
        "stateCd": state_id,
        "districtCd":district_id,
        "acNumber": assembly_id,
        "pageNumber": 0,
        "pageSize": 10
    }
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Origin": "https://voters.eci.gov.in",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "applicationname": "VSP",
        "atkn_bnd": "null",
        "channelidobo": "VSP",
        "content-type": "application/json",
        "platform-type": "ECIWEB",
        "rtkn_bnd": "null",
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }
    resp = requests.post(url, json=payload)

    if resp and resp.json().get('payload'):
        part_list_data = sorted([int(p['partNumber']) for p in resp.json()['payload']])
        print(f"Total parts found: {len(part_list_data)}")

        choice_text = input("Enter range of which pdfs you want to download (3 for only pdf number 3, 1:15 for all pdfs from 1 to 15 or 'all' for all of the pdfs:")
        if len(choice_text) == 1:
            return [int(choice_text)]
        elif choice_text.lower()=="all":
            return [i for i in range(1,len(part_list_data)+1)]
        else:
            start,end = int(choice_text.split(':')[0]), int(choice_text.split(':')[1])
            return [i for i in range(start,end+1)]
def get_pdf_url():
    pdf_choice = int(input(('''Enter corresponding number
1.Final Roll
2.Draft Roll
3.Supplement Roll (original)
4.General Election
Enter the number of your choice:''')))
    if pdf_choice == 1:  # Final Roll
        url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/generate-published-supplement"
    elif pdf_choice == 2:  # Draft Roll (Endpoint assumed based on pattern)
        url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/generate-published-eroll"
    elif pdf_choice == 3:  # Supplement Roll (original)
        url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/generate-published-supplement"
    elif pdf_choice == 4:  # General Election
        url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/generate-published-geroll"
    return url,pdf_choice
def download_pdfs(bool_is_supplement,pdf_url,state_id,district_id,assembly_id,pdf_parts,captcha_text,captcha_id,language_id): #final,draft and supplement roll
    payload = {
        "stateCd": state_id,
        "districtCd": district_id,
        "acNumber": assembly_id,
        "partNumberList": pdf_parts,
        "captcha": captcha_text,
        "captchaId": captcha_id,
        "langCd": language_id,
        "isSupplement": bool_is_supplement,
    }
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://voters.eci.gov.in",
        "Referer": "https://voters.eci.gov.in/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "applicationname": "VSP",
        "channelidobo": "VSP",
        "platform-type": "ECIWEB",
    }
    response = requests.post(pdf_url, json = payload, headers= headers)

    if response.ok:
        try:
            dir_path = os.path.join(output_folder, state_name, district_name, assembly_name)
            os.makedirs(dir_path, exist_ok=True)
            for i in range(len(response.json()['payload'])):
                fileUuid = response.json()['payload'][i]['fileUuid']
                bucketName = response.json()['payload'][i]['bucketName']
                fileName = response.json()['payload'][i]['refId']
                actual_pdf_url = f"https://gateway-voters.eci.gov.in/api/v1/printing-publish/get-published-file?imagePath={fileUuid}&bucketName={bucketName}"
                print("File url is",actual_pdf_url)

                payload = requests.get(actual_pdf_url).json()['payload']
                file_path = os.path.join(dir_path, f"{i + 1}_booth_{fileName}")
                open(file_path, "wb").write(base64.b64decode(payload + "==="))
                print(f"PDF saved in {file_path}")
        except Exception as e:
            print(f"Error while downloading pdfs:{e}")
    else:
        print("Error: ",response.json())



folder_name = input("Enter the folder name to store PDFs: ")
try:
    os.makedirs(folder_name, exist_ok=True)
    output_folder = folder_name
    print(f"PDFs will be stored in: {os.path.abspath(output_folder)}")
except OSError as e:
    print(f"Error creating folder {folder_name}: {e}. Please try again.")

def main():
    state_id,state_name = state_selection()
    district_id,district_name = district_selection(state_id)

    assembly_id,assembly_name = assembly_selection(state_id,district_id)
    language_id = language_selection(state_id,district_id, assembly_id)


    pdf_parts  = get_pdf_parts() #returns a list
    pdf_url,pdf_choice = get_pdf_url()
    bool_is_supplement = False
    if pdf_choice==3:
        bool_is_supplement = True

    captcha_id,captcha_text = download_and_solve_captcha()
    print("The captcha is: ",captcha_text)

    download_pdfs(bool_is_supplement,pdf_url,state_id,district_id, assembly_id, pdf_parts, captcha_text, captcha_id, language_id)

main()

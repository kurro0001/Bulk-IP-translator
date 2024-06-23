
import pandas as pd
import requests
import time
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk


#api used: https://api.iplocation.net/
def callingapi(ip):
    try:
        response = requests.get(f'https://api.iplocation.net/?ip={ip}&format=json')
        response.raise_for_status()
        data = response.json()
        if data.get('response_code') == '200':
            return ip, data
        else:
            print(f"Failed to fetch details for IP {ip}: {data.get('response_message')}")
            return ip, {'ip': ip, 'error': 'Failed to fetch details'}
    except requests.RequestException as e:  
        print(f"Error fetching details for IP {ip}: {e}")
        return ip, {'ip': ip, 'error': str(e)}

def fileprocessing(inputfile, outputfile, progress, statuslabel, timelabel, successlabel, failurelabel, speedlabel, max_workers):
    try:
        if inputfile.endswith('.xlsx'):
            df = pd.read_excel(inputfile, header=None, names=['IP'])
        elif inputfile.endswith('.csv'):
            df = pd.read_csv(inputfile, header=None, names=['IP'])
        else:
            statuslabel.config(text="Unsupported file type. Please use xlsx or csv file type.")
            return
    except Exception as e:
        print(f"Error reading input file: {e}")
        statuslabel.config(text="Error reading input file")
        return

    results = []
    progress['maximum'] = len(df['IP'])
    totalips = len(df['IP'])
    successfulips = 0
    failedips = 0
    print(f"Starting to process {totalips} IP addresses...\n")
    startingtime = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuremapping = {executor.submit(callingapi, ip): ip for ip in df['IP']}
        for i, future in enumerate(as_completed(futuremapping)):
            ip = futuremapping[future]
            try:
                ip, data = future.result()
                results.append(data)
                successfulips += 1
            except Exception as e:
                print(f"Error processing IP {ip}: {e}")
                results.append({'ip': ip, 'error': str(e)})
                failedips += 1
            progress['value'] = i + 1
            progress.update()
            successlabel.config(text=f"Successfully Checked IPs: {successfulips}")
            failurelabel.config(text=f"Failed to Check IPs: {failedips}")

            timetaken = time.time() - startingtime
            if timetaken > 0:
                speed = (i + 1) / timetaken
                speedlabel.config(text=f"IPs checked per second: {speed:.2f}")
            print(f"Processed {i + 1} out of {totalips} IPs", end='\r')

    print("\nProcessing complete.")
    endingtime = time.time()
    totaltimetaken = endingtime - startingtime
    timelabel.config(text=f"Total Time Taken: {totaltimetaken:.2f} seconds")
    resultsDF = pd.DataFrame(results)
    outputformat = outputformatvariable.get()  

    if outputformat == 'csv':
        ogoutput = outputfile.replace('.xlsx', '_DETAILS.csv').replace('.json', '_DETAILS.csv')
        try:
            resultsDF.to_csv(ogoutput, index=False)
            print(f"Results saved to {ogoutput}")
            statuslabel.config(text=f"Processing complete. Results saved to {ogoutput}")
        except Exception as e:
            print(f"error writing output file: {e}")
            statuslabel.config(text="error writing output file")
    elif outputformat == 'json':
        ogoutput = outputfile.replace('.xlsx', '_DETAILS.json').replace('.csv', '_DETAILS.json')
        try:
            resultsDF.to_json(ogoutput, orient='records', indent=4)
            print(f"Results saved to {ogoutput}")
            statuslabel.config(text=f"Processing complete. Results saved to {ogoutput}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            statuslabel.config(text="Error writing output file")

def ondrop(event):
    inputfile = event.data.strip('{}')
    if inputfile.endswith('.xlsx'):
        outputfile = inputfile.replace('.xlsx', '_IPdata.xlsx')
    elif inputfile.endswith('.csv'):
        outputfile = inputfile.replace('.csv', '_IPdata.csv')
    else:
        statuslabel.config(text="Unsupported file type. Please use Excel or CSV.")
        return
    statuslabel.config(text="Checking IPs...")
    progress.pack(pady=20)
    max_workers = int(maxworkersinput.get())
    fileprocessing(inputfile, outputfile, progress, statuslabel, timelabel, successlabel, failurelabel, speedlabel, max_workers)

def main():
    global root, progress, statuslabel, timelabel, successlabel, failurelabel, speedlabel, outputformatvariable, maxworkersinput
    root = TkinterDnD.Tk()
    root.title("Bulk IP Translator")
    fontstyle = ("Helvetica", 13) 
    root.geometry("600x450")
    
    label = tk.Label(root, text="Drag and drop an Excel or CSV file here", font=fontstyle)
    label.pack(pady=20)
    
    outputformatvariable = tk.StringVar(value='csv')  # Default value is 'csv'
    formatlabel = tk.Label(root, text="Select Output Format:")
    formatlabel.pack(pady=5)
    formatdropdown = ttk.OptionMenu(root, outputformatvariable, 'csv', 'csv', 'json')
    formatdropdown.pack(pady=5)
    
    maxworkerstext = tk.Label(root, text="Enter Max Workers:")
    maxworkerstext.pack(pady=5)
    maxworkersinput = tk.Entry(root)
    maxworkersinput.pack(pady=5)
    
    save_button = tk.Button(root, text="Save", command=save_max_workers)
    save_button.pack(pady=5)
    
    logoimage = Image.open("logo.png")
    logoimage = ImageTk.PhotoImage(logoimage)
    root.iconphoto(True, logoimage)
    
    statuslabel = tk.Label(root, text="")
    statuslabel.pack()
    
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    timelabel = tk.Label(root, text="")
    timelabel.pack()
    successlabel = tk.Label(root, text="")
    successlabel.pack()
    failurelabel = tk.Label(root, text="")
    failurelabel.pack()
    speedlabel = tk.Label(root, text="")
    speedlabel.pack()
    
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', ondrop)
    
    root.mainloop()

def save_max_workers():
    try:
        max_workers = int(maxworkersinput.get())
    except ValueError:
        maxworkersinput.delete(0, 'end')
        maxworkersinput.insert(0, 'Invalid Input')

if __name__ == "__main__":
    main()
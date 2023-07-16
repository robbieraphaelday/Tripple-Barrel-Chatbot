import os

with open('openai_api.txt', 'r') as f:
    openai_apikey = f.read().strip()

os.environ['OPENAI_API_KEY'] = openai_apikey

import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
import glob
import subprocess
import tkinter as tk
import pickle
from datetime import datetime
import pytz
import re
import tkinter as tk

# def barrel_one_message_setup():
#     #Allows you to set up message history for barrel one.
#     return messages

# def barrel_two_message_setup():
#     #Allows you to set up message history for barrel two.
#     return messages

# def barrel_three_message_setup():
#     #Allows you to set up message history for barrel three.
#     return messages

OPENAI_API_PATH = 'openai_api.txt'

def launch_dialog(last_assistant_message):
    user_input = [None]  # initialize user_input

    def get_text_and_close():
        user_input[0] = text_area.get("1.0", tk.END).strip()  # get text from text_area
        root.destroy()  # close the window

    root = tk.Tk()
    root.geometry("600x400")  # set the window size
    root.title("Last Assistant Message")

    text_area = tk.Text(root, width=80, height=20)  # adjust width and height as needed
    text_area.insert(tk.END, last_assistant_message)  # insert last_assistant_message into text_area
    text_area.pack()

    ok_button = tk.Button(root, text="OK", command=get_text_and_close)
    ok_button.pack()

    root.mainloop()  # start the event loop
    return user_input[0]  # return the user's input


def get_timestamp_pst():
    # Get current time in PST
    pst = pytz.timezone('America/Los_Angeles')
    datetime_pst = datetime.now(pst)

    # Convert datetime object to string
    timestamp_str = datetime_pst.strftime("%Y-%m-%d_%H-%M-%S")

    return timestamp_str


def regex_processor(text):
    # Define the pattern for numbered sections using a regular expression
    pattern = r'(?<=\n)(?=\d+\).)'

    # Split the text using the pattern
    sections = re.split(pattern, text, flags=re.DOTALL)

    # Filter out empty strings from the list
    sections = [section.strip() for section in sections if section.strip()]

    return sections


#Checks out contents of a json file and allows you to get previous bot outputs.
def get_dates():
    unit = input("Which unit do you want to load? ")
    unit_info = get_unit_info()

    if unit not in unit_info:
        print("\nInvalid unit entered. Please enter a valid unit.\n")
        return

    column_list = unit_info.get(unit, [])
    print(f"\nDates in unit {unit}: {column_list}\n")

    copy_spreadsheet(LESSON_PLAN_SPREADSHEET)

    while True:
        user_start = input("Press enter to start from the beginning or type the date you want to begin on: ")
        if user_start:
            if user_start in column_list:
                new_start_index = column_list.index(user_start)
                column_list = column_list[new_start_index:]
                break
            else:
                print("\nInvalid start date entered. Please enter a valid date from the list.\n")
        else:
            break

    while True:
        user_end = input("Press enter to end at the last date or type the date you want to end on (inclusive): ")
        if user_end:
            if user_end in column_list:
                new_end_index = column_list.index(user_end) + 1
                if new_end_index < len(column_list):
                    column_list = column_list[:new_end_index]
                    break
                else:
                    print("\nEnd date is beyond the available date range. Please enter a valid end date.\n")
            else:
                print("\nInvalid end date entered. Please enter a valid date from the list.\n")
        else:
            break

    print(f"\nFinal dates in unit {unit}: {column_list}\n")
    return column_list

def quitting_conversation(messages, first_barrel=False, second_barrel=False, third_barrel=False):
    print("\n\nExiting the chatbot.")
    time_stamp = get_timestamp_pst()
    if first_barrel:
        print(f"Writing 'output_files/first_barrel_{time_stamp}output.txt'")
        with open(f"output_files/first_barrel_{time_stamp}output.txt", "w") as outfile:
            for item in messages:
                outfile.write(f"Role: {item['role']}\n")
                outfile.write(f"Content: {item['content']}\n")
                outfile.write("\n")
    elif second_barrel:
        print(f"Writing 'output_files/second_barrel/second_barrel_{time_stamp}output.txt'")
        with open(f"output_files/second_barrel/second_barrel_{time_stamp}output.txt", "w") as outfile:
            for item in messages:
                outfile.write(f"Role: {item['role']}\n")
                outfile.write(f"Content: {item['content']}\n")
                outfile.write("\n")
    elif third_barrel:
        print(f"Writing 'output_files/third_barrel/third_barrel_{time_stamp}output.txt'")
        with open(f"output_files/third_barrel/third_barrel_{time_stamp}output.txt", "w") as outfile:
            for item in messages:
                outfile.write(f"Role: {item['role']}\n")
                outfile.write(f"Content: {item['content']}\n")
                outfile.write("\n")
    else:
        print(f"Writing 'output_files/no_barrel/{time_stamp}output.txt'")
        with open(f"output_files/no_barrel/{time_stamp}output.txt", "w") as outfile:
            for item in messages:
                outfile.write(f"Role: {item['role']}\n")
                outfile.write(f"Content: {item['content']}\n")
                outfile.write("\n")


def add_to_history(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages

def remove_from_history(messages, role, content):
    messages.remove({"role": role, "content": content})
    return messages

def remove_system_messages(messages):
    messages = [message for message in messages if message["role"] != "system"]
    return messages

def get_user_input():
    root = tk.Tk()
    root.title("Custom Value for Prompt Context")
    input_value = ['']  # Mutable container

    def submit():
        input_value[0] = text_widget.get("1.0", "end-1c")  # modify the content of the list
        root.destroy()

    text_widget = tk.Text(root, height=10, width=50)
    text_widget.pack()
    submit_button = tk.Button(root, text="Submit", command=submit)
    submit_button.pack()
    root.mainloop()
    return input_value[0]  # return the user input after the mainloop is over

def search_text_in_files(directory, text):
    file_paths = glob.glob(directory + '/*.txt')
    
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            content = file.read()
            if text in content:
                # Calculate the proportion through the text
                proportion = content.index(text) / len(content) * 100
                print(f"\nMatch found! Your excerpt is {proportion:.2f}% through the text.")
                
                # Open the corresponding PDF file
                pdf_file_name = os.path.basename(file_path).replace('.txt', '.pdf')
                pdf_file_path = os.path.join('pdfs', pdf_file_name)
                subprocess.run(['xdg-open', pdf_file_path])
                return
    
    print("\nNo exact match found.\n")

def get_openai_api_key():
    with open(OPENAI_API_PATH, "r") as f:
        return f.read().strip()

def chatbot(messages, model="gpt-4", temperature=0, max_tokens=1000):
    openai.api_key = get_openai_api_key()
    
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, max_tokens=max_tokens, temperature=temperature, messages=messages)
            return response['choices'][0]['message']['content']
        except openai.error.InvalidRequestError as e:
            if "maximum context length" in str(e):
                for i, msg in enumerate(messages):
                    if msg['role'] == 'user':
                        removed_message = messages.pop(i)
                        print(f"Removed message due to length: {removed_message}")
                        break  # break the for loop once a user message is removed
                continue  # retry with the reduced list of messages
            else:
                raise  # if it's some other error, raise it

def doc_loop(messages, query, docsearch):
    docs = docsearch.similarity_search(query)
    print(f"\nFound {len(docs)} similar documents\n")

    for doc in docs:
        print("\nDocument:\n", doc.page_content, "\n")
        user_input = input("\nAdd this document to prompt context? [y, n, or find] ")
        if user_input.lower() in ['y', 'yes']:
            messages = add_to_history(messages, "user", "Here is some context I've found, please consider when I prompt you in the future: " + doc.page_content)
        elif user_input.lower() == 'find':
            search_text_in_files('text_docs', doc.page_content)
            final_user_input = input("\nAdd this document to prompt context? [y or n or custom] ")
            if final_user_input.lower() in ['y', 'yes']:
                messages = add_to_history(messages, "user", "Here is some context I've found, please consider when I prompt you in the future: " + doc.page_content)
            elif final_user_input.lower() in ['custom']:
                a = get_user_input()
                print("\nCustom value added to prompt context: " + a + "\n\n")
                messages = add_to_history(messages, "user", "Here is some context I've found, please consider when I prompt you in the future: " + doc.page_content)
    return messages

def make_query(docsearch, messages, query=None, know_what_I_want=False):
    # Ask user if they want to make a new query
    if know_what_I_want == False:
        new_query = input("\nDo you want to make a new query? [y or n] ")
        if new_query.lower() in ['y', 'yes']:
            query = input("\nEnter your query: ")
            messages = doc_loop(messages, query, docsearch)
            return messages
        else:
            return messages
    elif know_what_I_want == True:
        messages = doc_loop(messages, query, docsearch)
        return messages
    
def first_barrel_conversation(messages, docsearch, new_query=None, query=None, know_what_I_want=False):
    while True:
        messages = make_query(docsearch, messages, query=query, know_what_I_want=know_what_I_want)
        # Once we're done with the query, we can start the conversation
        prompt = input("Enter your prompt to the Assistant: ")
        # We're doing a temp message because there is an option to nix the message later. Or really, there is an option to save it
        temp_messages = messages.copy()
        temp_messages.append({"role": "user", "content": prompt})
        chat_response = chatbot(temp_messages)
        print("\n----------\nAI Response:", chat_response, "\n----------\n")
        # Ask user if they want to save the prompt and response
        user_input = input("\nSave this prompt and chat to history [y or n]? Write 'gaslight' to gaslight the assistant. Write 'q' to quit and move on to Barrel Two without saving prompt or response: ")
        if user_input.lower() in ['y', 'yes']:
            messages = add_to_history(messages, "user", prompt)
            messages = add_to_history(messages, "assistant", chat_response)
            print("\n----------\nPrompt saved:", prompt, "\n----------\n")
            print("\n----------\nChat saved:", chat_response, "\n----------\n")
            user_input = input("Enter 'q' to quit and move on to barrel two. Enter 'c' to continue to querying: ")
            if user_input.lower() in ['q', 'quit']:
                quitting_conversation(messages, first_barrel=True)
                return messages
            elif user_input.lower() in ['c', 'continue']:
                print("Continuing to querying...")
                know_what_I_want = True
                query = input("Enter your new query: ")
            else:
                print("Invalid input, continuing to querying...")
                know_what_I_want = True
                query = input("Enter your new query: ")
        elif user_input == "gaslight":
            chat_response = launch_dialog(chat_response)
            print(chat_response)                
            user_input = input("Enter your prompt. Enter 'q' to quit and move on to the Second Barrel. Enter 'c' to save responses and continue to querying: ")
            if user_input.lower() in ['q', 'quit']:
                messages = add_to_history(messages, "user", prompt)
                messages = add_to_history(messages, "assistant", chat_response)
                print("\n----------\nPrompt saved:", prompt, "\n----------\n")
                print("\n----------\nChat saved:", chat_response, "\n----------\n")
                quitting_conversation(messages, first_barrel=True)
                return messages
            elif user_input.lower() in ['c', 'continue']:
                messages = add_to_history(messages, "user", prompt)
                messages = add_to_history(messages, "assistant", chat_response)
                print("\n----------\nPrompt saved:", prompt, "\n----------\n")
                print("\n----------\nChat saved:", chat_response, "\n----------\n")
                print("Continuing to querying...")
                know_what_I_want = True
                query = input("Enter your new query: ")
            else:
                messages = add_to_history(messages, "user", prompt)
                messages = add_to_history(messages, "assistant", chat_response)
                chat_response = chatbot(messages)
                print("\n----------\nAI Response:", chat_response, "\n----------\n")
                messages = add_to_history(messages, "assistant", chat_response)
                print("Continuing to querying...")
                know_what_I_want = True
                query = input("Enter your new query: ")
        else:
            print("Prompt and response not saved.")
            print("Continuing to querying...")
            user_input = input("Enter 'q' to quit and move on to barrel two. Enter 'c' to continue to querying: ")
            if user_input.lower() in ['c', 'continue']:
                know_what_I_want = True
                query = input("Enter your new query: ")
            elif user_input.lower() in ['q', 'quit']:
                quitting_conversation(messages, first_barrel=True)
                return messages

def second_barrel_conversation(messages, template):
    history = False
    while True:
        if history == False:
            print("Loading the second barrel...")
            messages = remove_system_messages(messages)
            messages = add_to_history(messages, "system", "You are going to create a new outline following a specific outline. Your outline will be used to create a blog article.")
            messages = add_to_history(messages, "user", f"You will be given a template to follow: \n\n{template}\n\nWhat you need to do is take your responses from me and outline them into a blog article with sections split by digit, closing parenthesis, and period as I've shown.")
            chat_response = chatbot(messages)
            print("\n----------\nAI Response:", chat_response, "\n----------\n")
            messages = add_to_history(messages, "assistant", chat_response)
            user_response = input("\nPress 'y' to accept, otherwise, enter your prompt: ")
            if user_response.lower() in ['y', 'yes']:
                quitting_conversation(messages, second_barrel=True)
                return messages
            history = True
        else:
            while True:
                messages = add_to_history(messages, "user", user_response)
                chat_response = chatbot(messages)
                print("\n----------\nAI Response:", chat_response, "\n----------\n")
                messages = add_to_history(messages, "assistant", chat_response)
                user_response = input("\nPress 'y' to submit, otherwise, enter your prompt: ")
                if user_response.lower() in ['y', 'yes']:
                    quitting_conversation(messages, second_barrel=True)
                    return messages

def third_barrel_conversation(messages):
    outline = messages[-1]["content"]
    print(f"This is the outline\n\n{outline}\n\n")
    chunks = regex_processor(outline)
    print("These are the chunks\n\n", chunks, "\n\n")
    messages = remove_system_messages(messages)
    messages = add_to_history(messages, "system", "You will be iterating through an outline. It's important for you to output text that is ready for publishing as a blog. It should not look like an outline after you are done.")
    while True: 
        paragraph_list = []
        for chunk in chunks:
            # chunks is a list, for each string in that list, I want to run chatbot() on it.
            messages = add_to_history(messages, "user", f"Please take the following text from my outline and turn it into a paragraph or two for my final blog article: \n\n{chunk}")
            paragraph = chatbot(messages)
            paragraph_list.append(paragraph)
            messages = add_to_history(messages, "assistant", paragraph)
            print("\n----------\nAI Response:", paragraph, "\n----------\n")

        return paragraph_list

def load_pickle(file):
    # Load the docsearch object from the pickle file
    with open(file, 'rb') as f:
        docsearch = pickle.load(f)
    print("\nLoaded embeddings from embeddings.pickle\n")
    return docsearch

def main():
    try:    
        messages = [{"role": "system", "content": "You are an AI assistant that is helping me tackle ethical dilemmas in the field of autonomous driving. It's very important to refer to the research I give you for context and tell me when you are using your knowledge and going beyond the material I have provided."}]
        docsearch = load_pickle('embeddings.pickle')

        #First Barrel
        messages = first_barrel_conversation(messages, docsearch)
        
        #Second Barrel
        messages = second_barrel_conversation(messages, "outline_template.txt")
        
        

        #Third Barrel
        blog = third_barrel_conversation(messages)
        n = 0
        timestamp = get_timestamp_pst()
        for paragraph in blog:
            n += 1
            print(f"Paragraph {n}: /n{paragraph}")
            with open(f"blog/blog_{timestamp}.txt", 'a') as f:
                f.write(f"Section: {n}\n")
                f.write(paragraph)
        print(f"Blog saved to blog/blog_{timestamp}.txt")
        print("Exiting the chatbot.")
    except KeyboardInterrupt:
        print("\n\nExiting the chatbot.")
        quitting_conversation(messages)
        return

if __name__ == "__main__":
    main()
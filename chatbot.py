import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url = "https://openrouter.ai/api/v1",
    api_key = os.environ["OPENROUTER_API_KEY"],
)

class ChatAgent:
    def __init__(self, model, N):
        self.model = model
        self.rolling_buffer = N
        self.messages = [
            {"role":"system", "content":"You are a helpful, precise and accurate assistant"}
        ]
        self.response_state = False
    def callModel(self):
        print("Chat started. Type 'exit' to quit.\n")
        while True:
            inp = input()
            if (inp == "exit"):
                print("You are exiting the chat! Goodbye!!")
                print('\n')
                break
            if (inp == '/reset'):
                self.messages = [
                    {"role":"system", "content":"You are a helpful, precise and accurate assistant"}
                ]
                continue
            if (inp == '/tokens'):
                print("Here is info about the usage")
                print('\n')
                if (self.response_state==False):
                    print("You have not initiated the chat! Tokens used:0")
                    print('\n')
                    print("End of usage info")
                    print('\n')
                    continue
                else:
                    print(response.usage)
                    print('\n')
                    print("End of usage info")
                    print('\n')
                    continue
            if (inp=='/compact'):
                temp = "Summarize all we have talked about till now"
                self.messages.append({"role": "user", "content":temp})
                response = client.chat.completions.create(
                    model = self.model,
                    messages = self.messages,
                )
                reply1 = response.choices[0].message.content
                self.messages.append({"role":'assistant', 'content':reply1})
                print(reply1)
                print('\n')
                del self.messages[1:-1]
                continue
            self.messages.append({"role":"user", "content" : inp})
            response = client.chat.completions.create(
                model = self.model,
                messages = self.messages,
            )
            self.response_state = True
            max_possible =  1+2*(self.rolling_buffer)
            reply = response.choices[0].message.content
            self.messages.append({"role":"assistant", "content":reply})
            print(reply)
            print('\n')
            if (len(self.messages)>max_possible):
                temp = "Summarize all we have talked about till now"
                self.messages.append({"role": "user", "content":temp})
                response = client.chat.completions.create(
                    model = self.model,
                    messages = self.messages,
                )
                reply1 = response.choices[0].message.content
                self.messages.append({"role":'assistant', 'content':reply1})
                print(reply1)
                print('\n')
                del self.messages[1:-1]
                

if __name__ == "__main__":
    entry = input("Enter the model of chatbot you want to use:\n(1) for Open Router's general free version\n(2) for openai free version\n(3) for NVIDIA nemotron free version\n")
    if (entry=='1'):
        model = "openrouter/free"
    elif (entry == '2'):
        model = "openai/gpt-oss-20b:free"
    elif (entry == '3'):
        model = "nvidia/nemotron-3-nano-30b-a3b:free"
    else:
        print("Invalid Choice!")
    chat = ChatAgent(model, 5)
    chat.callModel()
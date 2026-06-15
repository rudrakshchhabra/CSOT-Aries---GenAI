# CSOT GENAI 
## WEEK 2 

This week taught us many concepts like how to use tools in chat bots, how to make a UI in our terminal that looks very pleasing.

We also learnt different ways to implement using tools like web fetch to fetch info in English from a URL, get a detailed analysis of some papers, search on google using Serper and return the results after analysing the first site which pops up.

So first we imported all the python modules we needed for our project. Like os, openai, dotenv to get the basic functioning like we did last week. Then we imported modules like trafilatura to convert messy html from sites online to normal text. We also imported mcp so that we could use it to access alphaxiv to add and run our tools. We also imported requests that enabled us to search on the internet. We imported textual to get out TUI working.

Then we got our basic format of running OpenAI, and AlphaXiv servers. As defined in the problem statement, we used Serper to perform a web_search. This was specfically not given in the lessons so had to look at the syntax from the internet.

Then we wrote the function web_fetch which opens any URL and then provided its content to the user. Here as can be seen in the code we used Trafilatura to get the text out of the messy HTML the function gets(downloads) from the URL.

Now we get the functions working using MCP through AlphaXiv. And we use it to add (without defining) two functions search_paper and get_paper_details. This shows how using mcp saves us the effort for defining functions by hand and we can use mcp to add functions to our chatbot easily.

Then using another async definition we define the basic format of each of our function, providing its description and its parameters and everything to make everything clear.

Then we define our main chat loop that gets the responses. Here we defined what actions to perform in case of each of the function calls. After this we defined a function to trim history, in case we exceed the max turns specified earlier in the code. This reduces the context we have but ensures that the number of calls does not exceed and become too much draining out token budgets.

Finally what acc to me is the most fun part, we define the TUI and built it. Earlier also we had defined the colors for the responses. Now we built the basic foundation and applied styles and colors to the UI. Also developing functionalities like input into the chatbox using the enter key. We also defined the get response function which we learnt in build 3. Also developing key bindings for exiting, clearing history, clearing display etc. Then we finally our UI class which has all the functionalities that we developed.

It was a fun and busy week but we built something nice.
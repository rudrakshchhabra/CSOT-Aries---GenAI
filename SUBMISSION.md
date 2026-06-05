# GEN AI WEEK 1

The major help I got was from the resources given in the background section of the git page for this track and also the two intro builds.

Also, Gemini helped me get the links to the chatbot models since the deepseek one given on the git did not work.
It was outdated or something.

I had already made the setup during the starting phase making the env and gitignore files in my project folder.
So, I started with the basic setup that I learn by working on builds 1 and 2. I read in the instructions that instead of a function we had to make class for the chatbot.

So, I made the class and initialized it with the initial conditions, which largely resembled those which I used in build 2. The choosing model section was new so I had to define it using a parameter of the class, the value of which was defined by the user.
Also, this initializing section had some the initial message list and my check to ensure that we could get the tokens accurately.

After this I set up the main function method.
Here again, I used the while loop like I used in build2.
Also, for things like /reset, /tokens, I had already done that in build 2. So, it was all basic.

The only things to think about were the rolling buffer and the compaction.
So first I learnt about their exact meaning and functionality and implemented it using if statements and normal list deletion by slicing.

At last, I wrote the main execution zone, in which I asked the user what kind of model they wanted to use.
I have included 3 for now but it is easy enough to add an n number of models.The only thing I did not do was the streaming thing that was asked in the second part of the bonus as that required me to fundamentally change the structure of parts of my code.

I started CSOT quite late and having only 1 day to understand the builds and make the final object did not leave me enough time to make that as well and obviously I did not want AI or anything to do it for me so I stopped at including one bonus checklist point only.

Moreover, it was fun!Thanks Aries ig
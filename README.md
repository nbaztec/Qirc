Qirc
====

Qirc is an IRC bot built in Python

It is a simple bot with even simpler UI, currently in development phase.

Supports:
* Wikipedia
* Wolfram Alpha
* Google Searches
* Youtube Searches
* Thinkdigit Forum
* Urbandictionary
* Weather and Forecasting
* IP Tracing
* Geolocation
* Voting, Votekick and Votearma (kickban)
* An experimental game - Werewolf 
* Cleverbot
* Dice roll
* URL commands
* Reminder
* Seen
* Tell command for visitor messages that are delivered when a user arrives
* Vast set of verbs


And and a much hated 'Armageddon' command.
* A short arma command for selective kickban
* armarecover for quick recovery from Armageddon.

Help:
* Use !help to obtain a set of commands
* Use -h or --help within each command for help and switches (there are aplenty of those)


Eg:
```\>!help  
\>Enter <command> -h for help on the respective command  
\>Commands:    
\>    !help             Shows this help  
\>    !search, !s       Search for a term on various sites  
\>    !calc, !c         Perform some calculation  
\>    !define, !d       Get the meaning, antonyms, etc, for a term  
\>    !weather, !w      Get weather and forecasts for a location  
\>    !locate, !l       Locate a user, IP or coordinate  
\>    !url              Perform operation on an url,    
\>                      Use %N (max 5) to access an earlier url  
\>    !user             Perform operation related to user  
\>    !vote             Start a vote  
\>    !roll             Roll a dice  
\>    !game             Begin a game    
\>!search -h  
\>Options  
\>  -h, --help            show this help message  
\>  -p, --private         Get results in private  
\>  -t N, --result=N      Get the N'th result  
\>  -1, --single          Output single line of title  
\>  -g, --google          Search on Google [Default]  
\>  -i, --gimage          Search on Google Images  
\>  -y, --youtube         Search on Youtube  
\>  -w, --wiki            Search on Wikipedia  
\>  -m, --imdb            Search on IMDB  
\>  -f, --tdf             Search on TDF  
\>  -c CUSTOM, --custom=CUSTOM  
\>                        Search on a custom site  ```
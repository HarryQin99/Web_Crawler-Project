import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import unicodedata
import re
import matplotlib.pyplot as plt
import json
from numpy import arange


# open the json file and store all
# the name into a list called names
with open("tennis.json", 'r') as f:
    temp = json.loads(f.read())
names = []
for dictionary in temp:
    names.append(dictionary['name'].title())

# function used to calculate the score difference
# in one score
def calculating_diff(score):
    number1 = ''
    number2 = ''
    for i in range(len(score)):
        if score[i] != '-':
            number1 += score[i]
        else:
            break
    number2 = score[i+1:]
    number1 = int(number1)
    number2 = int(number2)
    diff = number1-number2
    return diff

# function used to find the points in a score set
# which are in the left and right of '-'
def find_two_point(score):
    number1 = ''
    number2 = ''
    output_list = []
    if score[0] != '(':
        for i in range(len(score)):
            if score[i] != '-':
                number1 += score[i]
            else:
                number2 = score[i+1:]
                break
    else:
        for i in range(1,len(score)):
            if score[i] != '-':
                number1 += score[i]
            else:
                number2 = score[i+1:-1]
                break
    number1 = int(number1)
    number2 = int(number2)
    output_list.append(number1)
    output_list.append(number2)
    return output_list

# function used to double check if the score set found by
# regular expression is a 'complete valid' one
def check_valid_score(scores):
    new_pattern = r'\(?\d{1,2}\-\d{1,2}\)?'
    winner = ''
    point1 = 0
    point2 = 0
    winner_dic = {'player1':0,'player2':0,'NoWinner':0}
    score_list = []
    score_list = re.findall(new_pattern,scores)
    count_game = 0
    for element in score_list:
        valid_score = 0
        output_list = []
        if element[0].isdigit():      
            point1 = find_two_point(element)[0]
            point2 = find_two_point(element)[1]
            if (point1>=6 or point2>=6) and abs(point1-point2)>=2:
                valid_score = 1
            if (point1 == 7 and point2 == 6) or (point1 == 6 and point2 == 7):
                valid_score = 1
            if point1>point2:
                winner = 'player1'
            elif point2>point1:
                winner = 'player2'
            count_game +=1
        if not element[0].isdigit():           
            point1 = find_two_point(element)[0]
            point2 = find_two_point(element)[1]
            if (point1>=7 or point2>=7) and abs(point1-point2)>=2:
                valid_score = 1
            winner = 'NoWinner'
        output_list = [valid_score, winner]
        if output_list[0] == 0:
            return False
        else:
            winner_dic[output_list[1]] +=1
    if winner_dic['player1'] == winner_dic['player2']:
        return False
    if count_game <= 1:
        return False         
    return True

# specify the initial page to crawl
base_url = 'http://comp20008-jh.eng.unimelb.edu.au:9889/main/'
seed_item = 'index.html'
seed_url = base_url + seed_item
page = requests.get(seed_url)
soup = BeautifulSoup(page.text, 'html.parser') 

visited = {}
visited[seed_url] = True


# remove index.html
links = soup.findAll('a')
seed_link = soup.findAll('a', href=re.compile("^index.html"))


# to_visit_relative = list(set(links) - set(seed_link))
to_visit_relative = [l for l in links if l not in seed_link]

# resolve to absolute urls
to_visit = []
for link in to_visit_relative:
    to_visit.append(urljoin(seed_url, link['href']))
    


records_task1 = []
records_task2 = []
# find all outbound links on succsesor pages and explore each one 
while (to_visit):
    record_list = []
    record_list2 = []
    valid = 1
    
    # consume the list of urls
    link = to_visit.pop(0)
    # need to concat with base_url, an example item <a href="catalogue/sharp-objects_997/index.html">
    page = requests.get(link)
    
    # scarping code goes here
    soup = BeautifulSoup(page.text, 'html.parser')
    result = soup.find("h1",{'class':"headline"})
    # append the URL and the headline to the record_list for task1
    record_list.append(link)
    record_list.append(result.text)
    records_task1.append(record_list)
    
    # the following coding is for task2 find first named player and 
    # first complete valid score
    # find the whole article
    article = soup.find('div',{'id':"articleDetail"})
    article_total = ''
    player_dic = {} 
    index_list = []
    country = []
    # use the name list to find if the player name in the article
    for player in names:
        a = re.search(player,article.text)
        if a != None:
            index_list.append(a.start())
            player_dic[a.start()] = player



    # if no player name in the article, it would be a 'invalid article'
    if index_list == []:
        valid = 0
        
    # use regular expression to find the Scores Sets in the article
    pattern = r'(?:(?:[6-7]-[0-6]\ ?)|(?:[0-6]-[6-7]\ ?)|(?:[\(]\d{1,2}[-|\/]\d{1,2}[\)]\ ?)){2,8}(?:\d{1,2}-\d{1,2})?'
    
    # use re.findall to find all the scores satisfied the regular expression
    if re.findall(pattern,article.text):
        all_scores_list = re.findall(pattern,article.text)
    else:
        valid = 0
    
    # find the first complete score from the all the scores sets 
    # found by regular expression by using 
    # the function 'check_valid_score()'
    valid_score = ''
    if valid != 0:
        for score in all_scores_list:
            if check_valid_score(score):
                valid_score = score
                break


    # if none of them is complete, this article would be a 'invalid article'
    if valid_score == '':
        valid = 0
    
    # append information need of task2 just for 'valid article'
    if valid != 0:
        player = player_dic[sorted(index_list)[0]]
        record_list2.append(link)
        record_list2.append(result.text)
        record_list2.append(player.upper())
        record_list2.append(valid_score)
        records_task2.append(record_list2)
    
    # mark the item as visited, i.e., add to visited list, remove from to_visit
    visited[link] = True
    new_links = soup.findAll('a')          
    # add new absolute url to to_visit list
    for new_link in new_links:
        new_item = new_link['href']
        new_url = urljoin(link, new_item)
        if new_url not in visited and new_url not in to_visit:
            to_visit.append(new_url)

# store the data scraped for tast1 to a dataframe and a csv file
column_names = ["url", "headline"]
tennis_data = pd.DataFrame(records_task1, columns = column_names,)
tennis_data.to_csv('task1.csv',index = False) 

# store the data scraped for tast2 as a dataframe and a csv file
column_names2 = ['url','headline','player','score']
tennis_data2 = pd.DataFrame(records_task2, columns = column_names2,)
tennis_data2.to_csv('task2.csv',index = False)


# following coding is for task3, looking for the
# average difference
new_pattern = r'\(?\d{1,2}\-\d{1,2}\)?'
dic_record_difference = {}
dic_num_diff = {}

# use two dictionaries to store all the difference of game and the amount of the
# games he plays
for record in records_task2:
    difference = 0
    score =record[3]
    b = re.findall(new_pattern,score)
    for element in b:
        element = element.strip()
        if element[0].isdigit():
            difference += calculating_diff(element)
    if record[2] in dic_record_difference.keys():
        dic_record_difference[record[2]].append(abs(difference))
        dic_num_diff[record[2]] += 1
    else:
        dic_record_difference[record[2]] = [abs(difference)]
        dic_num_diff[record[2]] = 1
        
# calculate the avg_diff for each player and store his name 
# and avg_diff into a list 
records_task3 = [] 
dic_avg_player = {}    
for name in dic_record_difference.keys():
    total_diff = 0
    record = []
    record.append(name)
    for diff in dic_record_difference[name]:
        total_diff += diff
    avg_diff = total_diff/dic_num_diff[name]
    dic_avg_player[name] = avg_diff
    record.append(avg_diff)
    records_task3.append(record)

# store the data for task3 as dataframe and csv file
column_names3 = ['player','avg_game_difference']
tennis_data3 = pd.DataFrame(records_task3, columns = column_names3,)
tennis_data3.to_csv('task3.csv',index = False)

# store the corresponding frequence of the article wrriten about
# each player
dic_player_freq = {}
for record in records_task2:
    name = record[2]
    if name in dic_player_freq:
        dic_player_freq[name.upper()] +=1
    else:
        dic_player_freq[name.upper()] = 1
value_list = []
for value in dic_player_freq.values():
    value_list.append(value)
player_list = []
freq_list = []

# find five player that articles are most frequently written
# about and the number of article about them
for num in sorted(value_list)[-5:]:
    for name in dic_player_freq.keys():
        if dic_player_freq[name] == num and not (name in player_list):
            player_list.append(name)
            freq_list.append(num)


# plot a bar graph to show for task4
plt.bar(arange(len(freq_list)),freq_list,width = 0.8)
plt.xticks(arange(len(player_list)),player_list,rotation = 15)
plt.xlabel('Player_name')
plt.ylabel('Amount of articles')
plt.title("Task4 Top 5 Players_article wrriten about - frequence")
plt.savefig('task4.png',dpi = 200,bbox_inches='tight')
plt.clf()

# store the win percentage for each play in a dictionary
dic_name_percentage = {}
for dictionary in temp:
    dic_name_percentage[dictionary['name']] = dictionary['wonPct']


# store corresponding average game difference and win percentage
# for each player 
dic_percentage_name = {}
_avg_percentage = []
for record in records_task3:
    record5 = []
    player_name = record[0]
    win_perc = float(dic_name_percentage[player_name][:5])
    if win_perc in dic_percentage_name:
        dic_percentage_name[win_perc].append(player_name)
    else:
        dic_percentage_name[win_perc] = [player_name]

# store the win_percentage and average game difference for each player 
# and follow by the order of win_percentage, from smallest to largest#
records_task5 = []
for percentage in sorted(dic_percentage_name):
    for name in dic_percentage_name[percentage]:
        record = []
        record.append(name)
        record.append(dic_avg_player[name])
        record.append(percentage)
        records_task5.append(record)

# store the data for task5 as dataframe
column_names5 = ['player','avg','percentage']
tennis_data5 = pd.DataFrame(records_task5, columns = column_names5,)

# draw a barplot with two y_axis to record the win_percnetage and 
# average_difference for each player
x = arange(len(tennis_data5['player']))
ax1 = plt.subplot(1,1,1)
w = 0.4
plt.xticks(x + w /2,tennis_data5['player'] , rotation='vertical')
avg =ax1.bar(x, tennis_data5['avg'], width=w, color='b', align='center')
ax1.set_ylabel('avg_diff')
ax2 = ax1.twinx()
percentage =ax2.bar(x + w, tennis_data5['percentage'], width=w,color='r',align='center')
ax2.set_ylabel('win_percentage(%)')
plt.legend([avg, percentage],['avg_diff', 'win_percentage'])
plt.title("Task5 Avg_deiff / Win_percentage - player")
plt.xlabel('player_name')
plt.savefig('task5.png',dpi= 200,bbox_inches='tight')

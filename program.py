## REMEMBER TO SET PARAMETERS IN SECTION "RUN PROGRAM"

import datetime, time, praw, sqlite3, json, urllib.request, dropbox

### Parsing data from CoinMarketCap ### -----------------------------

def parse_cmc():
    try:
        cmc_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=300'
        with urllib.request.urlopen(cmc_url) as b:
                source = b.read().decode('utf-8')
                cmc = json.loads(source)
        display("*** SUCCESSFUL URL REQUEST FROM CMC")
        return cmc
    except:
        display("[ERROR]: During parsing data from CMC")

# Creating library: key = ticker, value = name
def create_dict(cmc):
    exceptions = ["OK", "FUN", "PRO", "ATM", "LINK", "TIME", "SHIFT",
                  "ST", "DAT", "SC", "POLL", "LA", "KORE", "PRE", "MED",
                  "FAIR", "RISE", "INK", "LEND", "REP", "PPY", "DATA",
                  "SMART", "CAG", "SNT", "RISE", "PAY"]
    black_list = ["RISE", "RLC"]
    coins = {}
    for item in cmc:
            ticker = str(item['symbol'])
            name = str(item['name'])
            if len(ticker) >= 2:
                    if ticker in black_list:
                            pass
                    elif ticker not in exceptions:
                            coins[ticker] = name
                    else:
                            coins[name] = name
    return coins

# Get price of the coin
def get_price(name, cmc):
    for item in cmc:
        if name == item["name"]:
            return float(item["price_usd"])

### Upload to Dropbox ### -------------------------------------------

def dropbox_upload(filename, destiantion):
    token = 'eqg5tu9rCjcAAAAAAAAD7FWNwuOBojYi5L-FsdRzJ5CMG2bA9ewfM9ILF7o_PVIP'
    d = dropbox.Dropbox(token)
    file = open(filename, "rb")        ## Open file
    d.files_upload(file.read(), destiantion, mode=dropbox.files.WriteMode.overwrite)

### SQLite ### ------------------------------------------------------

## conn = sqlite3.connect('database.db')
## c = conn.cursor()

def create_table():
    command = '''CREATE TABLE IF NOT EXISTS Data (name TEXT, datetime TEXT,
    posts REAL, mentions REAL, totalm REAL, percent REAL, price REAL)'''
    c.execute(command)

def delete_table():
    c.execute("DROP TABLE Data")

### Display + save to log file ### ------------------------------------

def display(text):
    print(text)
    file.write(text+"\n")

### Authorize, Select subreddit w. sort settings ### ----------------

def authenticaton():
    try:
        reddit = praw.Reddit(client_id = 'lYDJQDb5uVhpqg',
                             client_secret = 'uV5YiUui5ohYlXbdiRnrK6UwMKc',
                             username = 'matikka96',
                             password = 'muumipappa69',
                             user_agent = 'hahaha')

        subreddit = reddit.subreddit('CryptoCurrency').new(limit=1000)
        return subreddit            ## Return subreddit ovject
    except:
        display("[ERROR] Authentication request.\n")

### Saving titles (last 24h) in to title_list ### -------------------

def save_titles(subreddit, interval):
    counter = 1
    title_list = []
    time_scan = time.time()
    for item in subreddit:
        try:
            if (time_scan - item.created_utc) < interval:  ## 1 day
                # display("{}\t{}\t{}\t{}\t{}\n".format(counter, time_scan,
                # item.created_utc,(time_scan-item.created_utc), item.title[0:80]))
                title_list.append(str(item.title))
                counter += 1
        except:
            #display("[ERROR] Reading titles.\n")
            pass
    display("*** TITLES SAVED TO LIST \t[{}] Titlecount".format(len(title_list)))
    return title_list           ## Return list of titles

### Scanning titles for mentions ### --------------------------------

def scan_titles(coins, title_list):
    coins_mentioned = []
    total_mentions = 0
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for coin in coins:
        mentions = 0
        for title in title_list:
            if (title.find(coins[coin]) + title.find(coin)) > -2:
                mentions += 1
                total_mentions += 1
                # try:
                #     display("{}\t{}".format(coin, title))
                # except:
                #     display("******** CODEC ERROR ********")
                #     pass
        if mentions > 0:
#            display ("{} TOTAL MENTIONS {} \n".format(coin, mentions))
            coins_mentioned.append(str(coin))
            price = get_price(str(coins[coin]), cmc)
#            display("{} - {}".format(coin, price))
            c.execute('''INSERT INTO Data (name, datetime, posts, mentions, price) VALUES (?, ?, ?, ?, ?)''',
              (coin, dt, len(title_list), mentions, price))
            conn.commit()

    # Inserting total mentions + calculating popularity percentage
    command = "UPDATE Data SET totalm = ? WHERE datetime = ?"
    c.execute(command, (total_mentions, dt))
    c.execute("UPDATE Data SET percent = ROUND(mentions / totalm * 100, 2)")
    conn.commit()
    display("*** DATABASE UPDATED \t\t[{}] Coin mentions".format(total_mentions))


### PARAMETERS ### --------------------------------------------------

interval = 86400                            ## Run interval [s]
db_name = "database_d.db"                   ## Database name for saving
log_name = "log_d.txt"                      ## logfile name for saving

### RUN PROGRAM ### -------------------------------------------------

file = open(log_name, "a")                  ## Open logfile
conn = sqlite3.connect(db_name)             ## Connect to database
c = conn.cursor()
start = time.time()
start_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")               ## Start time
display('''---------------------------------------------
TIME \t{}'''.format(start_date))
cmc = parse_cmc()                           ## Request json from Coinmarketcap.com
coins = create_dict(cmc)                    ## Save coins to list
create_table()                              ## Create table in database
subreddit = authenticaton()                 ## Reddit Authentication
title_list = save_titles(subreddit, interval)   ## Save titles to list
scan_titles(coins, title_list)              ## Scan titles for coin mentions
duration = time.time() - start              ## Run duration
display("RUN DURATION {}s\n".format(round((duration), 2)))
file.close()                                ## Closing logfile
conn.close()                                ## Closing database
# dropbox_upload(log_name, "/Raspberry/crypto/asd.txt")   ## Upload logfile
# dropbox_upload(db_name, "/Raspberry/crypto/asd.db")     ## Upload database

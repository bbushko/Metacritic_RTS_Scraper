import csv
from bs4 import BeautifulSoup
import requests
from time import sleep

HOST = 'https://www.metacritic.com'
URL = 'https://www.metacritic.com/browse/games/genre/metascore/real-time/all?view=detailed&page=0'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}
CSV = 'data.csv'


def request_and_soup(url, params):
    """Function returns scrapable page for bs4."""
    r = requests.get(url, headers=HEADERS, params=params)  #  making request to the page
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup
    else:
        print('Something went wrong...')
        return


def get_num_pages(soup):
    """We want to get the number of pages at the beginning of scraping"""
    num_pages = soup.find('li', class_='last_page').find(class_='page_num').get_text(strip=True)
    print(f"Number of pages for current platform: {num_pages}")
    return int(num_pages)


def get_links(soup):
    """This function get links for every game on the page to scrape."""
    links = []
    games = soup.find_all('td', class_='clamp-summary-wrap')
    for game in games:
        # we do not need unscored games data, so exclude it.
        if game.find('div', class_='metascore_w large game tbd'):
            continue
        links += [HOST + game.find('a', class_='title')['href']]
    return links


def get_content(soup):
    """Returns a dictionary with data from the page (we've got its URL with get_links(soup))"""
    # The most frequent exception we met is the absence of user reviews. Therefore, handle it there.
    user_reviews = soup.find('div', class_='details side_details').find('span', class_='count').find('a')
    if user_reviews:
        game_data = [{
            'Title': soup.find('h1').get_text(strip=True),
            'Platform': soup.find('span', class_='platform').get_text(strip=True),
            'Release_Date': soup.find('li', class_='summary_detail release_data').find('span', class_='data').get_text(
                strip=True),
            'Metascore': soup.find('span', itemprop='ratingValue').get_text(strip=True),
            'User_Score': soup.find('div', class_='metascore_w').get_text(strip=True),
            'Num_Critic_Reviews': soup.find('span', class_='count').find('a').span.get_text(strip=True).split(' ')[0],
            'Num_User_Reviews': user_reviews.get_text(strip=True).split(' ')[0],
            'Developer': soup.find('li', class_='summary_detail developer').find('a', class_='button').get_text(
                strip=True),
            'Genre': [genre.get_text(strip=True) for genre in
                      soup.find('li', class_='summary_detail product_genre').find_all('span', class_='data')]
        }]
    else:
        game_data = [{
            'Title': soup.find('h1').get_text(strip=True),
            'Platform': soup.find('span', class_='platform').get_text(strip=True),
            'Release_Date': soup.find('li', class_='summary_detail release_data').find('span', class_='data').get_text(
                strip=True),
            'Metascore': soup.find('span', itemprop='ratingValue').get_text(strip=True),
            'User_Score': None,
            'Num_Critic_Reviews': soup.find('span', class_='count').find('a').span.get_text(strip=True).split(' ')[0],
            'Num_User_Reviews': None,
            'Developer': soup.find('li', class_='summary_detail developer').find('a', class_='button').get_text(
                strip=True),
            'Genre': [genre.get_text(strip=True) for genre in
                      soup.find('li', class_='summary_detail product_genre').find_all('span', class_='data')]
        }]

    return game_data


def save_data(items, path):
    with open(path, 'a+', newline='') as data_file:
        writer = csv.writer(data_file, delimiter=',')
        for item in items:
            writer.writerow([item['Title'], item['Platform'], item['Release_Date'], item['Metascore'],
                             item['User_Score'],
                             item['Num_Critic_Reviews'],
                             item['Num_User_Reviews'],
                             item['Developer'],
                             item['Genre']])


def create_file(path):
    with open(path, 'w', newline='') as data_file:
        writer = csv.writer(data_file, delimiter=',')
        writer.writerow(['Title',
                         'Platform',
                         'Release_Date',
                         'Metascore',
                         'User_Score',
                         'Num_Critic_Reviews',
                         'Num_User_Reviews',
                         'Developer',
                         'Genre'])
    return path


def parser():
    """Parsing multiple pages with requests params"""
    soup_start = request_and_soup(URL, params='')
    pagination = get_num_pages(soup_start)
    data_file = create_file('rts_data.csv')
    for page in range(0, pagination):
        print(f'\nParsing page {page}/{pagination}')
        current_soup = request_and_soup(URL, params={'page': page})
        current_links = get_links(current_soup)
        for link in current_links:
            try:
                print('Parsing ' + link)
                blocks = []
                soup_link = request_and_soup(link, params='')
                blocks.extend(get_content(soup_link))
                save_data(blocks, data_file)
            except AttributeError as error:
                print(f"Something is missing for {link}")
                print(error)
                continue
        sleep(3)


if __name__ == '__main__':
    parser()

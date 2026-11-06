import concurrent.futures
import sys
import time
import requests

HN_API = "https://hacker-news.firebaseio.com/v0"

def usage(status=0):
    print(f'''Usage: {sys.argv[0]} [-w WORKERS] [-b]

    -w WORKERS  Number of threads (default: 16)
    -b          Compare imperative, functional, and concurrent versions
    -h          Show this help message''')
    sys.exit(status)

def fetch_story(story_id):
    try:
        return requests.get(f"{HN_API}/item/{story_id}.json", timeout=10).json() or {}
    except requests.RequestException:
        return {}

def is_story(item):
    return item.get("type") == "story"

def scrape_imperative(story_ids):
    stories = []
    for story_id in story_ids:
        story = fetch_story(story_id)
        if is_story(story):
            stories.append(story)
    stories.sort(key=lambda s: s.get("score", 0), reverse=True)
    return stories

def scrape_functional(story_ids):
    items = map(fetch_story, story_ids)
    return sorted(filter(is_story, items), key=lambda s: s.get("score", 0), reverse=True)

def scrape_concurrent(story_ids, workers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        items = list(executor.map(fetch_story, story_ids))
    return sorted(filter(is_story, items), key=lambda s: s.get("score", 0), reverse=True)

def timed(name, scrape, *args):
    start = time.time()
    stories = scrape(*args)
    print(f"{name}: {time.time() - start:.2f} seconds")
    return stories

def main():
    workers = 16
    benchmark = False
    arguments = sys.argv[1:]

    while arguments and arguments[0].startswith('-'):
        argument = arguments.pop(0)
        if argument == '-w': 
            workers = int(arguments.pop(0))
        elif argument == '-b':
            benchmark = True
        elif argument == '-h':
            usage(0)
        else:
            usage(1)

    if arguments or workers < 1:
        usage(1)

    story_ids = requests.get(f"{HN_API}/topstories.json", timeout=10).json()

    if benchmark:
        timed("Imperative", scrape_imperative, story_ids)
        timed("Functional", scrape_functional, story_ids)
        timed(f"Concurrent ({workers} threads)", scrape_concurrent, story_ids, workers)
        return

    stories = timed(f"Concurrent ({workers} threads)", scrape_concurrent, story_ids, workers)

    print("\nTop 10 Stories on Hacker News:")
    for index, story in enumerate(stories[:10], 1):
        link = story.get("url", f"https://news.ycombinator.com/item?id={story['id']}")
        print(f"{index}. {story['title']} - {story.get('score', 0)} points")
        print(f"   {link}")

if __name__ == '__main__':
    main()

import tomllib
import sqlite3
import shutil
import re
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import date, datetime, time, timedelta
from markdown_generator import MarkdownGenerator


def parse_toml(toml_file='pyproject.toml'):
    with open(toml_file, "rb") as f:
        data = tomllib.load(f)
        return data['posts']

def db_connect(config):
    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()
    return cursor

def get_post_ids(db):
    query = 'select id from posts'
    try:
        results = db.execute(query)
        rows = results.fetchall()
    except Exception as e:
        print(f'ERROR: Failed to retrieve post IDs from DB: [{e}]')
        exit(70)
    return rows

def get_post_data(db,post_id,data_type):
    queries = {
        "body"  : "select header, content from bodies where post_id=?",
        "hints" : "select content from hints where post_id=?",
        "attrs" : "select title, publish_date, draft, tags, difficulty, subtitle from posts where id=?"
    }
    try:
        results = db.execute(queries[data_type], (post_id,))
        rows = results.fetchall()
    except Exception as e:
        print(f'ERROR: Failed to retrieve post {data_type} from DB for post ID [{post_id}]: [{e}]')
        exit(72)
    return rows

def purge_publish_dir(config):
    verify_working_dir()
    publish_dir = Path(f'../{config['publish_dir']}')

    if not publish_dir.is_dir():
        print(f'ERROR: Ensure publish dir [{publish_dir}] exists and is a directory.')
        exit(75)

    for item in publish_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

def verify_working_dir():
    cwd = Path.cwd().name
    images_dir = Path("../content/images")

    if not images_dir.is_dir() or cwd != 'scripts':
        print("Can't identify site root directory. Make sure this script is being run from [<site_root>/scripts/].")
        exit(75)

def create_post_dir(post_id):
    verify_working_dir()
    post_dir = Path(f'../content/{post_id}')
    if not post_dir.is_dir():
        try:
            post_dir.mkdir()
        except Exception as e:
            print(f'ERROR: failed to create post dir for post [{post_id}] [{e}]')
            exit(73)

def create_post_index(post_id, post_content):
    verify_working_dir()
    index_file = f'../content/{post_id}/index.md'
    try:
        with open(index_file, "w") as f:
            f.write(post_content)
    except Exception as e:
        print(f"ERROR: Failed to create index file [{index_file}] [{e}]")
        exit(74)

def hide_post_images():
    verify_working_dir()
    image_dir = Path('../content/images')

    if not image_dir.is_dir():
        print('ERROR: Could not find image directory to hide/unhide images.')
        exit(76)

    for image_file in image_dir.glob('*.jpg'):
        if re.match(f'^[0-9]+', image_file.name):
            base_name = image_file.name
            new_name = image_file.with_name(f'.{base_name}')
            image_file.rename(new_name)

def unhide_post_images(post_id):
    verify_working_dir()
    image_dir = Path('../content/images')

    if not image_dir.is_dir():
        print('ERROR: Could not find image directory to hide/unhide images.')
        exit(77)

    for image_file in image_dir.glob('*.jpg'):
        if re.match(f'^\\.{post_id}\\-', image_file.name):
            base_name = image_file.name
            new_name = image_file.with_name(f'{base_name[1:]}')
            image_file.rename(new_name)
   
def should_print_hints(publish_date):
    # we want to wait until after noon on the publish date to print the hints section
    timezone = ZoneInfo('America/New_York')
    publish_date = date.fromisoformat(publish_date)
    now = datetime.now(timezone)
    if publish_date < now.date():
        return True
    elif publish_date == now.date() and now.time() >= time(12, 0):        
        return True
    else:
        return False

def should_print_location(publish_date):
    # we want to wait until the day after the publish date to print the location section
    timezone = ZoneInfo('America/New_York')
    publish_date = date.fromisoformat(publish_date)
    now = datetime.now(timezone)
    if publish_date < now.date():
        return True
    return False


def main():
    # parse config file
    config = parse_toml()

    # connect to DB
    db = db_connect(config)

    # init markdown object
    md = MarkdownGenerator()
    
    # optionally purge the publish directory
    if config['purge_publish_dir'] == True:
        print(f'🗑️  Purging publish dir [{config['publish_dir']}]', end='...')
        purge_publish_dir(config)
        print('done. ✅')
    
    # hide all post images. we will then unhide them as we build the posts
    print('🫥  Hiding all post images', end='...')
    hide_post_images()
    print('done. ✅')

    # loop through post IDs
    for post_id in get_post_ids(db):
        
        # gather post info from DB
        post_id = post_id[0]
        post_attrs = get_post_data(db, post_id, 'attrs')[0]
        post_body = get_post_data(db, post_id, 'body')
        post_hints = get_post_data(db, post_id, 'hints')
        
        if 'expiration_days' in config:
            expiration_date = datetime.strptime(post_attrs[1], "%Y-%m-%d") + timedelta(days=config['expiration_days'])
            expiration_date = expiration_date.strftime("%Y-%m-%d")
        else:
            expiration_date = ''

        print(f'🪧  Creating post [{post_id}] [{post_attrs[0]}]', end='...')
        
        # build markdown
        md.front_matter(title=f'🔎 #{post_id} - {post_attrs[0]}', date=post_attrs[1], draft=post_attrs[2], tags=post_attrs[3], expiration_date=expiration_date)
        md.subtitle(post_attrs[5])
        md.difficulty_badge(post_attrs[4])
        md.photo(alt='Find', path=f'../images/{post_id}-find.jpg')
        if len(post_body) > 0:
            post_body = post_body[0]
            md.body(header=post_body[0], text=post_body[1])
        if len(post_hints) > 0:
            post_hints = post_hints
            md.hints(post_hints)

        if should_print_location(publish_date=post_attrs[1]):
            md.location(post_id)
        else:
            md.location_message()

        # create post
        create_post_dir(post_id)
        create_post_index(post_id, md.output())
        unhide_post_images(post_id)

        print('done. ✅')

        # clear the markdown buffer to prepare for the next post
        md.clear()


if __name__ == "__main__":
    main()

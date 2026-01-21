from datetime import date
import sqlite3
import tomllib
import json
import typer


app = typer.Typer(help="Blog post management CLI")


def parse_toml(toml_file='pyproject.toml'):
    with open(toml_file, "rb") as f:
        data = tomllib.load(f)

    return data['posts']


def validate_date_callback(_date):
    # this separate validate wrapper is necessary because a typer.Option(callback=func) passes in different
    # args depending on how many args your callback function has registered.
    if not validate_date(_date):
        raise typer.BadParameter('Invalid date format. Use YYYY-MM-DD.')
    else:
        return _date


def validate_date(_date):
    try:
        publish_date = date.fromisoformat(_date)
    except ValueError:
        return False
    
    return True


def validate_difficulty_callback(diff):
    # this separate validate wrapper is necessary because a typer.Option(callback=func) passes in different
    # args depending on how many args your callback function has registered.
    if not validate_difficulty(diff):
        raise typer.BadParameter(f"Invalid difficulty [{diff}]. Choose from {valid_difficulties}")
    else:
        return diff


def validate_difficulty(diff):
    config = parse_toml()
    if diff.lower() not in config['valid_difficulties']:
        return False

    return True


def db_connect():
    config = parse_toml()
    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()
    return (conn, cursor)


def insert_post(post):
    db = db_connect()
    db_conn = db[0]
    db_cur = db[1]

    # set the difficulty as the first tag
    tags = f'{post['difficulty']} {" ".join(post['tags'])}'
    post_query = 'insert into posts (title,tags,publish_date,difficulty,subtitle) values (?,?,?,?,?)'
    db_cur.execute(post_query, (post['title'], tags, post['publish_date'], post['difficulty'], post['subtitle']))

    post_id = db_cur.lastrowid
    
    if post['body'] or post['body_header']:
        body_query = 'insert into bodies (post_id, header, content) values(?, ?, ?)'
        db_cur.execute(body_query, (post_id, post['body_header'], post['body']))
    
    if post['hints']:
        for hint in post['hints']:
            hints_query = 'insert into hints (post_id, content) values(?, ?)'
            db_cur.execute(hints_query, (post_id, hint))

    db_conn.commit()
    db_conn.close()


@app.command()
def create(
    title: str = typer.Option(..., "-t", "--title",  help="Title of the post"),
    subtitle: str = typer.Option(None, "-s", "--subtitle",  help="Subtitle of the post. Will be displayed just below the title."),
    publish_date: str = typer.Option(..., "-p", "--publish-date", help="The post will be published on this date. (YYYY-MM-DD)", callback=validate_date_callback),
    difficulty: str = typer.Option(..., "-d", "--difficulty", help="Difficulty of finding the object", callback=validate_difficulty_callback),
    body: str = typer.Option(None, "-b", "--body", help="The body of the post"),
    body_header: str = typer.Option(None, "--body-header", help="The header of the body"),
    hints: list[str] = typer.Option([], "-h", "--hint", help="Hint for finding the object. (repeatable, e.g., --hint hint1 --hint hint2)"),
    tags: list[str] = typer.Option([], "--tag", help="Tag for the post. (repeatable, e.g., --tag tag1 --tag tag2) [NOTE: <difficulty> is automatically set as a tag]")
):

    post_dict = {}
    post_dict['title'] = title
    post_dict['subtitle'] = subtitle
    post_dict['publish_date'] = publish_date
    post_dict['difficulty'] = difficulty
    post_dict['body'] = body
    post_dict['body_header'] = body_header
    post_dict['hints'] = hints
    post_dict['tags'] = tags

    print(json.dumps(post_dict, indent=2))
    insert_post(post_dict)


@app.command()
def create_interactive():

    # Prompt for values
  
    title = typer.prompt("Post title (required)")

    subtitle = typer.prompt("Post subtitle", default='', show_default=False)
    
    while True:
            publish_date = typer.prompt("Publish date (required) (YYYY-MM-DD)")
            if validate_date(publish_date):
                break
            typer.echo(f"❌ Invalid date format. Please use YYYY-MM-DD.")
    
    while True:
            difficulty = typer.prompt("Difficulty (required)").lower()
            if validate_difficulty(difficulty):
                break
            typer.echo(f"❌ Invalid difficulty. Please choose from {valid_difficulties}.")

    body_header = typer.prompt("Body header", default='', show_default=False)

    body = typer.prompt("Body", default='', show_default=False)

    tags = []
    print("Enter zero or more tags. Enter an empty tag when finished.")
    while True:
        tag = typer.prompt("Tag", default='', show_default=False).lower()
        if not tag:
            break
        tags.append(tag)

    hints = []
    print("Enter zero or more hints. Enter an empty hint when finished.")
    while True:
        hint = typer.prompt("Hint", default='', show_default=False).lower()
        if not hint:
            break
        hints.append(hint)


    post_dict = {}
    post_dict['title'] = title
    post_dict['subtitle'] = subtitle
    post_dict['publish_date'] = publish_date
    post_dict['difficulty'] = difficulty
    post_dict['body'] = body
    post_dict['body_header'] = body_header
    post_dict['hints'] = hints
    post_dict['tags'] = tags
    post_dict

    print(json.dumps(post_dict, indent=2))

    typer.prompt("Press ENTER to accept these values, CTRL+C to cancel.", default='', show_default=False)

    insert_post(post_dict)

if __name__ == "__main__":
    app()
